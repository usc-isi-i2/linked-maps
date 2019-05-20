import psycopg2
import osgeo.ogr
from psycopg2.extensions import AsIs
import json
import time

COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[32m"
COLOR_CYAN = "\033[36m"
COLOR_YELLOW = "\033[33m"
VERBOSE = True
VERBOSE_PRINT_SQL = False

def VPRINT(pstring):
    global VERBOSE
    if VERBOSE: print(COLOR_CYAN + pstring + COLOR_RESET)

def VPRINTSQL(pstring):
    global VERBOSE_PRINT_SQL
    if VERBOSE_PRINT_SQL: print(COLOR_YELLOW + pstring + COLOR_RESET)

class Segment:
    # create class (connect to database, create tables if user asks)
    def __init__(self, config_path, is_reset = False):
        try:
            config = json.load(open(config_path, "r"))
        except Exception as e:
            print("cannot load config file, ERROR: %s" % str(e))
            exit(-1)

        try:
            self.dbname             = config["dbname"]
            self.user               = config["user"]
            self.host               = config["host"]
            self.map_table_name     = config["map_table_name"]
            self.same_as_table_name = config["same_as_table_name"]
            self.contain_table_name = config["contain_table_name"]
            self.geom_table_name    = config["geom_table_name"]
            self.SRID               = config["SRID"]
        except LookupError:
            print("invalid config JSON")
            exit(-1)

        try:
            self.connection = psycopg2.connect(dbname   = self.dbname,
                                               user     = self.user,
                                               host     = self.host)
            print(COLOR_GREEN + "Connected to database successfully" + COLOR_RESET)
        except psycopg2.Error as e:
            print("Unable to connect to the database: %s" % str(e))
            exit(-1)

        if is_reset:
            self.create_starting_table()

    # perform SQL commit (change tables)
    def sql_commit(self):
        self.connection.commit()

    def create_starting_table(self):
        # TODO Add FK to table
        # WTF is FK?

        cur = self.connection.cursor()
        SQL = '''
        DROP TABLE IF EXISTS %s;
        DROP TABLE IF EXISTS %s;
        DROP TABLE IF EXISTS %s;
        DROP TABLE IF EXISTS %s;
        create table %s (
            id SERIAL NOT NULL PRIMARY KEY, 
            line_name  VARCHAR(256),
            gid INTEGER,
            isLeaf BOOL
        );
        create table %s (
            gid SERIAL NOT NULL PRIMARY KEY,
            wkt VARCHAR
        );
        select AddGeometryColumn(%s, 'geom', %s, 'MULTILINESTRING', 2);
        create table %s (
            id1 INTEGER,
            id2 INTEGER
        );
        create table %s (
            par_id INTEGER,
            child_id INTEGER
        );
        '''

        cur.execute(SQL,
                    (AsIs(self.map_table_name),
                     AsIs(self.geom_table_name),
                     AsIs(self.same_as_table_name),
                     AsIs(self.contain_table_name),
                     AsIs(self.map_table_name),
                     AsIs(self.geom_table_name),
                     self.geom_table_name,
                     self.SRID,
                     AsIs(self.same_as_table_name),
                     AsIs(self.contain_table_name))
                    )

        VPRINTSQL(str(cur.query))
        self.sql_commit()

    # create new map segment entry
    def add_new_map(self, fname, map_name):
        cursor = self.connection.cursor()
        shapefile = osgeo.ogr.Open(fname)
        SQL = '''
        DROP TABLE IF EXISTS %s; 
        CREATE TABLE %s (gid SERIAL NOT NULL PRIMARY KEY);
        SELECT AddGeometryColumn(%s, 'geom', %s, 'MULTILINESTRING', 2);
        '''

        table_name = "_" + map_name
        cursor.execute(SQL, (AsIs(table_name), AsIs(table_name), table_name, self.SRID,))
        VPRINTSQL(str(cursor.query))

        layer = shapefile.GetLayer(0)

        SQL_2 = '''
        INSERT INTO %s (geom) VALUES (ST_MULTI(ST_GeometryFromText(%s, %s)))
        '''

        total_feature_count_in_map = layer.GetFeatureCount()
        for i in range(total_feature_count_in_map):
            feature = layer.GetFeature(i)
            # name = feature.GetField("NAME").decode("Latin-1")
            # TODO: optimize
            wkt = feature.GetGeometryRef().ExportToWkt()
            cursor.execute(SQL_2, (AsIs(table_name), wkt, self.SRID))
            # VPRINTSQL(str(cursor.query))
        VPRINT("Added %d Geometry lines to %s" % (total_feature_count_in_map, table_name))
        

        INSERT_NEW_MAP = '''
            INSERT INTO %s (wkt, geom)
            SELECT ST_ASTEXT(ST_UNION(geom)), ST_UNION(geom)
            FROM %s
            RETURNING gid;
        '''
        cursor.execute(INSERT_NEW_MAP, (
            AsIs(self.geom_table_name),
            AsIs(table_name)))
        VPRINTSQL(str(cursor.query))

        gid = cursor.fetchone()[0]
        cursor.execute("DROP TABLE %s", (AsIs(table_name),))
        # VPRINTSQL(str(cursor.query))

        INSERT_TO_MAP_TABLE = '''
            INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id;
        '''
        cursor.execute(INSERT_TO_MAP_TABLE, (AsIs(self.map_table_name), table_name, gid))
        id = cursor.fetchone()[0]
        VPRINTSQL(str(cursor.query))
        self.sql_commit()

        return id

    def get_all_leaf_nodes(self):
        SQL = '''
        SELECT id FROM %s WHERE isLeaf = TRUE
        '''

        cur = self.connection.cursor()
        cur.execute(SQL, (AsIs(self.map_table_name),))
        return [t[0] for t in cur.fetchall()]

    # create the segment (called from main)
    def do_segment(self, path_to_shape_file, map_name, verbose = False):
        global VERBOSE
        VERBOSE = verbose

        VPRINT("Start segment map %s..." % map_name)
        start_time = time.time()
        id = self.add_new_map(path_to_shape_file, map_name)
        VPRINT("Map %s successfully added to row id %s" % (map_name, id))
        leaf_nodes_id = self.get_all_leaf_nodes()
        VPRINT("New map will segment with %d leaf nodes: {%s}" % (len(leaf_nodes_id), ",".join((str(e) for e in leaf_nodes_id))))

        if id != 1:
            # Old Intersect New, New Intersect Old
            for r in leaf_nodes_id:
                if r == id:
                    continue
                curr_timer_meas = time.time()
                new_id_a = self.intersect(r, id)
                VPRINT("finished intersect row %d and row %d resulting in row %d (took %.2f seconds)" % (r, id, new_id_a, (time.time() - curr_timer_meas)))
                curr_timer_meas = time.time()
                new_id_b = self.intersect(id, r)
                VPRINT("finished intersect row %d and row %d resulting in row %d (took %.2f seconds)" % (id, r, new_id_b, (time.time() - curr_timer_meas)))
                self.insert_same_as(new_id_a, new_id_b)
                self.insert_contain(r, new_id_a)
                self.insert_contain(id, new_id_b)

            # Old Minus New
            for r in leaf_nodes_id:
                if r == id:
                    continue
                curr_timer_meas = time.time()
                new_id = self.minus(r, id)
                VPRINT("finished row %d minus row %d resulting in row %d (took %.2f seconds)" % (r, id, new_id, (time.time() - curr_timer_meas)))
                self.insert_contain(r, new_id)

            # New Minus ST_UNION(Old)
            curr_timer_meas = time.time()
            new_id = self.union_minus(id)
            VPRINT("finished union row %d resulting in row %d (took %.2f seconds)" % (id, new_id, (time.time() - curr_timer_meas)))
            self.insert_contain(id, new_id)

            # Update old leaf node to be false
            self.update_leaf(id)
            VPRINT("Finished segmenting map %s (took %.2f seconds)\n" % (map_name, (time.time() - start_time)))

    # create a same_as entry
    def insert_same_as(self, id_a, id_b):
        SQL = '''
            INSERT INTO %s (id1, id2) VALUES (%s, %s)
        '''
        cur = self.connection.cursor()
        cur.execute(SQL, (AsIs(self.same_as_table_name), id_a, id_b))
        VPRINTSQL(str(cur.query))

    # create a contain entry
    def insert_contain(self, par_id, child_id):
        SQL = '''
            INSERT INTO %s (par_id, child_id) VALUES (%s, %s)
        '''
        cur = self.connection.cursor()
        cur.execute(SQL, (AsIs(self.contain_table_name), par_id, child_id))
        VPRINTSQL(str(cur.query))

    # mark entries with older id's as not-leaf anymore
    def update_leaf(self, id):
        cur = self.connection.cursor()
        cur.execute("UPDATE %s SET isLeaf = FALSE WHERE id <= %s", (AsIs(self.map_table_name), id))
        VPRINTSQL(str(cur.query))

    # create an intersection entry
    def intersect(self, id_a, id_b):
        """
        do intersection between id_a and id_b
        add gid to map table
        if id_a link to empty geom -> do nothing
        :return: new_id of map table
        """
        cur = self.connection.cursor()
        # check gid of id_a and gid of id_b
        cur.execute("SELECT gid, line_name FROM %s WHERE id = %s", (AsIs(self.map_table_name), id_a))
        gid_a, name_a = cur.fetchone()

        cur.execute("SELECT gid, line_name FROM %s WHERE id = %s", (AsIs(self.map_table_name), id_b))
        gid_b, name_b = cur.fetchone()

        if gid_a != 0 and gid_b != 0:

            SQL = '''
                INSERT INTO %s (wkt, geom) 
                SELECT ST_ASTEXT(res.lr), lr
                FROM(
                    SELECT ST_MULTI(ST_INTERSECTION(
                        l.geom, 
                        ST_INTERSECTION(
                            st_buffer(l.geom, 0.0015), 
                            st_buffer(r.geom, 0.0015))         
                    )) as lr
                    FROM 
                        (
                        SELECT geom
                        FROM %s, %s
                        WHERE %s.gid = %s.gid and %s.id = %s
                        ) as l,
                        (
                        SELECT geom
                        FROM %s, %s
                        WHERE %s.gid = %s.gid and %s.id = %s
                        ) as r
                ) res
                where ST_geometrytype(res.lr) = 'ST_MultiLineString'
                RETURNING gid
            
            '''
            cur.execute(SQL,
                (AsIs(self.geom_table_name),
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.map_table_name),
                 id_a,
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.map_table_name),
                 id_b))

            new_gid = cur.fetchone()
            # VPRINTSQL(str(cur.query))

            if new_gid:
                new_gid = new_gid[0]
                cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                                     (AsIs(self.map_table_name),
                                      name_a,
                                      new_gid))
            else:
                cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                            (AsIs(self.map_table_name),
                             name_a,
                             0))
            # VPRINTSQL(str(cur.query))
        else:
            cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                                 (AsIs(self.map_table_name),
                                  name_a,
                                  0))
            # PRINTSQL(str(cur.query))
        new_id = cur.fetchone()[0]
        # TODO: update sameAs and Contain
        return new_id

    # create a MAP-MINUS-MAP entry
    def minus(self, id_a, id_b):
        cur = self.connection.cursor()
        # check gid of id_a and gid of id_b
        cur.execute("SELECT gid, line_name FROM %s WHERE id = %s", (AsIs(self.map_table_name), id_a))
        gid_a, name_a = cur.fetchone()
        cur.execute("SELECT gid, line_name FROM %s WHERE id = %s", (AsIs(self.map_table_name), id_b))
        gid_b, name_b = cur.fetchone()

        if gid_a == 0:
            cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                                 (AsIs(self.map_table_name),
                                  name_a,
                                  0))
        elif gid_b == 0:
            cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                                 (AsIs(self.map_table_name),
                                  name_a,
                                  gid_a))
        else:
            SQL = '''
                INSERT INTO %s (wkt, geom) 
                SELECT ST_ASTEXT(res.lr), lr
                FROM(
                    SELECT ST_MULTI(ST_INTERSECTION(
                        l.geom, 
                        ST_DIFFERENCE(
                            st_buffer(l.geom, 0.0015), 
                            st_buffer(r.geom, 0.0015))         
                    )) as lr
                    FROM 
                        (
                        SELECT geom
                        FROM %s, %s
                        WHERE %s.gid = %s.gid and %s.id = %s
                        ) as l,
                        (
                        SELECT geom
                        FROM %s, %s
                        WHERE %s.gid = %s.gid and %s.id = %s
                        ) as r
                ) res
                where ST_geometrytype(res.lr) = 'ST_MultiLineString'
                RETURNING gid

            '''
            cur.execute(SQL,
                (AsIs(self.geom_table_name),
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.map_table_name),
                 id_a,
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.geom_table_name),
                 AsIs(self.map_table_name),
                 AsIs(self.map_table_name),
                 id_b))
            new_gid = cur.fetchone()
            # VPRINTSQL(str(cur.query))
            if new_gid:
                new_gid = new_gid[0]
                cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                                     (AsIs(self.map_table_name),
                                      name_a,
                                      new_gid))
            else:
                cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                                     (AsIs(self.map_table_name),
                                      name_a,
                                      0))
            # VPRINTSQL(str(cur.query))
        new_id = cur.fetchone()[0]
        return new_id

    # create a UNION-MINUS-MAP entry
    def union_minus(self, id):
        cur = self.connection.cursor()
        cur.execute("SELECT gid, line_name FROM %s WHERE id = %s", (AsIs(self.map_table_name), id))
        gid, name = cur.fetchone()

        SQL = '''
            INSERT INTO %s (wkt, geom) 
            SELECT ST_ASTEXT(res.lr), lr
            FROM(
                SELECT ST_MULTI(ST_INTERSECTION(
                    l.geom, 
                    ST_DIFFERENCE(
                        st_buffer(l.geom, 0.0015), 
                        st_buffer(r.geom, 0.0015))         
                )) as lr
                FROM 
                    (
                    SELECT geom
                    FROM %s, %s
                    WHERE %s.gid = %s.gid and %s.id = %s
                    ) as l,
                    (
                    SELECT geom
                    FROM %s, %s
                    WHERE %s.gid = %s.gid and %s.id < %s and %s.isLeaf = True
                    ) as r
            ) res
            where ST_geometrytype(res.lr) = 'ST_MultiLineString'
            RETURNING gid

        '''
        cur.execute(SQL,
            (AsIs(self.geom_table_name),
             AsIs(self.geom_table_name),
             AsIs(self.map_table_name),
             AsIs(self.geom_table_name),
             AsIs(self.map_table_name),
             AsIs(self.map_table_name),
             id,
             AsIs(self.geom_table_name),
             AsIs(self.map_table_name),
             AsIs(self.geom_table_name),
             AsIs(self.map_table_name),
             AsIs(self.map_table_name),
             id,
             AsIs(self.map_table_name)))
        new_gid = cur.fetchone()[0]
        cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                             (AsIs(self.map_table_name),
                              name,
                              new_gid))
        new_id = cur.fetchone()[0]
        return new_id