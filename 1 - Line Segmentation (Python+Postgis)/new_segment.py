import psycopg2
import osgeo.ogr
from psycopg2.extensions import AsIs
import json
import time

'''
    2/13/19
    Patavee Meemeng
    We see the problem that previous segment algo can't represent all the 
    changes analysis we want. This program will do ONLY difference. To illustrate,
    we have map A. When map B comes we do ST_DIFFERENCE with A. When maps C comes,
    we do the ST_DIFFERENCE from C to A and B. This also miss some change analysis
    that previous algorithm can do, such as "segment that stay the same from A->B
    but change in C.
'''


class Segment:
    def __init__(self, config_path, is_reset=False):
        try:
            config = json.load(open(config_path, "r"))
        except Exception as e:
            print "cannot load config file, ERROR: ", e
            exit(-1)

        try:
            self.dbname = config["dbname"]
            self.user = config["user"]
            self.password = config["password"]
            self.host = config["host"]
            self.map_table_name =config["map_table_name"]
            self.same_as_table_name = config["same_as_table_name"]
            self.contain_table_name = config["contain_table_name"]
            self.geom_table_name =config["geom_table_name"]
            self.SRID = config["SRID"]
        except LookupError:
            print "invalid config JSON"
            exit(-1)

        try:
            self.connection = psycopg2.connect(dbname=self.dbname,
                                               user=self.user,
                                               password=self.password,
                                               host=self.host)
            print "connect to db successfully"
        except psycopg2.Error as e:
            print "I am unable to connect to the database", e
            exit(-1)

        if is_reset:
            self.create_starting_table()

    def commit(self):
        self.connection.commit()

    def create_starting_table(self):
        # TODO Add FK to table

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

        layer = shapefile.GetLayer(0)

        SQL_2 = '''
        INSERT INTO %s (geom) VALUES (ST_MULTI(ST_GeometryFromText(%s, %s)))
        '''

        for i in range(layer.GetFeatureCount()):
            feature = layer.GetFeature(i)
            # name = feature.GetField("NAME").decode("Latin-1")
            wkt = feature.GetGeometryRef().ExportToWkt()
            cursor.execute(SQL_2, (AsIs(table_name), wkt, self.SRID))

        INSERT_NEW_MAP = '''
            INSERT INTO %s (wkt, geom)
            SELECT ST_ASTEXT(ST_UNION(geom)), ST_UNION(geom)
            FROM %s
            RETURNING gid;
        '''
        cursor.execute(INSERT_NEW_MAP, (
            AsIs(self.geom_table_name),
            AsIs(table_name)))

        gid = cursor.fetchone()[0]
        cursor.execute("DROP TABLE %s", (AsIs(table_name),))

        INSERT_TO_MAP_TABLE = '''
            INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id;
        '''
        cursor.execute(INSERT_TO_MAP_TABLE, (AsIs(self.map_table_name), table_name, gid))
        id = cursor.fetchone()[0]
        return id

    def get_all_leaf_nodes(self):
        SQL = '''
        SELECT id FROM %s WHERE isLeaf = TRUE
        '''

        cur = self.connection.cursor()
        cur.execute(SQL, (AsIs(self.map_table_name),))
        return [t[0] for t in cur.fetchall()]

    def do_segment(self, path_to_shape_file, map_name, verbose=False):
        if verbose:
            print "***Start segment map {} ...".format(map_name)
        start = time.time()
        id = self.add_new_map(path_to_shape_file, map_name)
        if verbose:
            print "Map {} successfully added to row id {}".format(map_name, id)
        leaf_nodes_id = self.get_all_leaf_nodes()
        if verbose:
            print "New map will segment with {} leaf nodes: {}".format(len(leaf_nodes_id),
                                                                       " ".join((str(e) for e in leaf_nodes_id)))
        if id != 1:
            # Old Intersect New, New Intersect Old
            for r in leaf_nodes_id:
                if r == id:
                    break

                new_id_a = self.intersect(r, id)
                if verbose:
                    print "finished intersect row {} and row {} resulting in row {}".format(r, id, new_id_a)

                new_id_b = self.intersect(id, r)
                if verbose:
                    print "finished intersect row {} and row {} resulting in row {}".format(id, r, new_id_b)

                self.insert_same_as(new_id_a, new_id_b)
                self.insert_contain(r, new_id_a)
                self.insert_contain(id, new_id_b)

            # Old Minus New
            for r in leaf_nodes_id:
                if r == id:
                    break
                new_id = self.minus(r, id)
                if verbose:
                    print "finished  row {} minus row {} resulting in row {}".format(r, id, new_id)

                self.insert_contain(r, new_id)

            # New Minus ST_UNION(Old)
            new_id = self.union_minus(id)
            if verbose:
                print "finished union row {} resulting in row {}".format(id, new_id)

            self.insert_contain(id, new_id)

            # Update old leaf node to be false
            self.update_leaf(id)
            if verbose:
                print "***Finished segment map {} in {} seconds\n".format(map_name, str(time.time() - start))

    def insert_same_as(self, id_a, id_b):
        """

        :param id_a:
        :param id_b:
        :return:
        """

        SQL = '''
            INSERT INTO %s (id1, id2) VALUES (%s, %s)
        '''
        cur = self.connection.cursor()
        cur.execute(SQL, (AsIs(self.same_as_table_name), id_a, id_b))


    def insert_contain(self, par_id, child_id):
        """

        :param id_a:
        :param id_b:
        :return:
        """

        SQL = '''
            INSERT INTO %s (par_id, child_id) VALUES (%s, %s)
        '''
        cur = self.connection.cursor()
        cur.execute(SQL, (AsIs(self.contain_table_name), par_id, child_id))


    def update_leaf(self, id):
        cur = self.connection.cursor()
        cur.execute("UPDATE %s SET isLeaf = FALSE WHERE id <= %s", (AsIs(self.map_table_name), id))

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
        else:
            cur.execute("INSERT INTO %s (line_name, gid, isLeaf) VALUES (%s, %s, TRUE) RETURNING id",
                                 (AsIs(self.map_table_name),
                                  name_a,
                                  0))
        new_id = cur.fetchone()[0]
        # TODO: update sameAs and Contain
        return new_id

    def minus(self, id_a, id_b):
        """
        :param id_a:
        :param id_b:
        :return:
        """
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
        new_id = cur.fetchone()[0]
        return new_id

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