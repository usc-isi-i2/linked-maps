"""
This class is a part of the line segmentation algorithm.

TODO: revise this...
This Node class is abstraction of nodes in segmentation tree.
Each node contains its name, metadata, and a "pointer" pointed the geometric it represents.
Also, since it is a node in graph, it will contain its parents and children.
This would increase the flexibility of changing the segmentation algorithm in the future.
"""

from mykgutils import fclrprint
from json import load
from psycopg2 import connect, Error as psycopg2_error
from postgis_sqls import sql_str_reset_all_tables
from osgeo.ogr import Open as ogr_open



# wrapper function used to verify necessary information before doing intersect, union etc operation
def verify(func):
    def inner(*args, **kwargs):
        if args[0].metadata != args[1].metadata:
            print("ERROR: Metadata Mismatched")
            return None

        if args[0] == args[1]:
            print("ERROR: Same Node")
            return None

        if args[0].name == args[1].name:
            print("ERROR: Same Name")
            return None
        return func(*args, **kwargs)

    return inner


class Node:
    def __init__(self, metadata, gid, name):
        self.metadata = metadata
        self.gid = gid
        self.name = name
        self.parent = dict()  # parentname : node object
        self.child = dict()  # childname : node object

    def __repr__(self):
        return "name : {}, parent: {}, child: {}".format(self.name, self.parent.keys(), self.child.keys())

    @verify
    def intersect(self, other_node, new_name, buff=0.0015):
        cur = self.metadata.connection.cursor()
        SQL = '''
            INSERT INTO %s (wkt, geom) 
            SELECT ST_ASTEXT(res.lr), lr
            FROM(
                SELECT ST_MULTI(ST_INTERSECTION(
                    l.geom, 
                    ST_INTERSECTION(
                        st_buffer(l.geom, %s), 
                        st_buffer(r.geom, %s))         
                )) as lr
                FROM 
                    (
                    SELECT geom
                    FROM %s
                    WHERE %s.gid = %s
                    ) as l,
                    (
                    SELECT geom
                    FROM %s
                    WHERE %s.gid = %s
                    ) as r
            ) res
            where ST_geometrytype(res.lr) = 'ST_MultiLineString'
            RETURNING gid

        '''
        cur.execute(SQL,
                    (AsIs(self.metadata.table_name),
                     AsIs(buff),
                     AsIs(buff),
                     AsIs(self.metadata.table_name),
                     AsIs(self.metadata.table_name),
                     AsIs(self.gid),
                     AsIs(self.metadata.table_name),
                     AsIs(self.metadata.table_name),
                     AsIs(other_node.gid),
                     ))

        new_gid = cur.fetchone()
        new_node = Node(self.metadata, new_gid, new_name)

        self.child[new_name] = new_node
        other_node.child[new_name] = new_node
        new_node.parent[self.name] = self
        new_node.parent[other_node.name] = other_node

        return new_node

    @verify
    def union(self, other_node, new_name, buff=0.0015):
        cur = self.metadata.connection.cursor()
        SQL = '''
            INSERT INTO %s (wkt, geom) 
            SELECT ST_ASTEXT(res.lr), lr
            FROM(
                SELECT ST_MULTI(ST_INTERSECTION(
                    l.geom, 
                    ST_UNION(
                        st_buffer(l.geom, %s), 
                        st_buffer(r.geom, %s))         
                )) as lr
                FROM 
                    (
                    SELECT geom
                    FROM %s
                    WHERE %s.gid = %s
                    ) as l,
                    (
                    SELECT geom
                    FROM %s
                    WHERE %s.gid = %s
                    ) as r
            ) res
            where ST_geometrytype(res.lr) = 'ST_MultiLineString'
            RETURNING gid

        '''
        cur.execute(SQL,
                    (AsIs(self.metadata.table_name),
                     AsIs(buff),
                     AsIs(buff),
                     AsIs(self.metadata.table_name),
                     AsIs(self.metadata.table_name),
                     AsIs(self.gid),
                     AsIs(self.metadata.table_name),
                     AsIs(self.metadata.table_name),
                     AsIs(other_node.gid),
                     ))

        new_gid = cur.fetchone()
        new_node = Node(self.metadata, new_gid, new_name)

        # Note: Union Operation shall not result in any graph relations

        # self.child[new_name] = new_node
        # other_node.child[new_name] = new_node
        # new_node.parent[self.name] = self
        # new_node.parent[other_node.name] = other_node

        return new_node

    @verify
    def minus(self, other_node, new_name, buff=0.0015):
        cur = self.metadata.connection.cursor()
        SQL = '''
            INSERT INTO %s (wkt, geom) 
            SELECT ST_ASTEXT(res.lr), lr
            FROM(
                SELECT ST_MULTI(ST_INTERSECTION(
                    l.geom, 
                    ST_DIFFERENCE(
                        st_buffer(l.geom, %s), 
                        st_buffer(r.geom, %s))         
                )) as lr
                FROM 
                    (
                    SELECT geom
                    FROM %s
                    WHERE %s.gid = %s
                    ) as l,
                    (
                    SELECT geom
                    FROM %s
                    WHERE %s.gid = %s
                    ) as r
            ) res
            where ST_geometrytype(res.lr) = 'ST_MultiLineString'
            RETURNING gid

        '''
        cur.execute(SQL,
                    (AsIs(self.metadata.table_name),
                     AsIs(buff),
                     AsIs(buff),
                     AsIs(self.metadata.table_name),
                     AsIs(self.metadata.table_name),
                     AsIs(self.gid),
                     AsIs(self.metadata.table_name),
                     AsIs(self.metadata.table_name),
                     AsIs(other_node.gid),
                     ))

        new_gid = cur.fetchone()
        new_node = Node(self.metadata, new_gid, new_name)

        self.child[new_name] = new_node
        new_node.parent[self.name] = self

        # Note: New node should not be child of other_node (because of minus operation)
        # other_node.child[new_name] = new_node
        # new_node.parent[other_node.name] = other_node

        return new_node

    @classmethod
    def from_shapefile(cls, path, metadata, name):
        cursor = metadata.connection.cursor()
        shapefile = ogr_open(path)
        SQL = '''
        DROP TABLE IF EXISTS %s; 
        CREATE TABLE %s (gid SERIAL NOT NULL PRIMARY KEY);
        SELECT AddGeometryColumn(%s, 'geom', %s, 'MULTILINESTRING', 2);
        '''

        table_name = "temp"
        cursor.execute(SQL, (AsIs(table_name), AsIs(table_name), table_name, metadata.SRID,))
        layer = shapefile.GetLayer(0)

        SQL_2 = '''
        INSERT INTO %s (geom) VALUES (ST_MULTI(ST_GeometryFromText(%s, %s)))
        '''

        total_feature_count_in_map = layer.GetFeatureCount()
        for i in range(total_feature_count_in_map):
            feature = layer.GetFeature(i)
            wkt = feature.GetGeometryRef().ExportToWkt()
            cursor.execute(SQL_2, (AsIs(table_name), wkt, metadata.SRID))

        INSERT_NEW_MAP = '''
            INSERT INTO %s (wkt, geom)
            SELECT ST_ASTEXT(ST_UNION(geom)), ST_UNION(geom)
            FROM %s
            RETURNING gid;
        '''
        cursor.execute(INSERT_NEW_MAP, (
            AsIs(metadata.table_name),
            AsIs(table_name)))

        gid = cursor.fetchone()[0]
        cursor.execute("DROP TABLE %s", (AsIs(table_name),))

        metadata.connection.commit()
        node = cls(metadata, gid, name)
        return node


class PostGISChannel:
    def __init__(self, config_path, verbosity, reset_tables=False):
        ''' Initialize PostGISChannel, used to communicate with PostGIS Backend (via SQL). '''

        # verbosity for easier debugability
        self.verbosity = verbosity

        # load config file
        try:
            config = load(open(config_path, "r"))
        except Exception as e:
            print("Cannot load configuration file, ERROR: %s" % str(e))
            exit(-1)

        # load config parameters
        try:
            self.dbname             = config["dbname"]
            self.user               = config["user"]
            self.host               = config["host"]
            self.geom_table_name    = config["geom_table_name"]
            self.map_table_name     = config["map_table_name"]
            self.contain_table_name = config["contain_table_name"]
            self.SRID               = config["SRID"]
        except LookupError:
            print("Invalid configuration file")
            exit(-1)

        # establish connection
        try:
            self.connection = connect(dbname=self.dbname,
                                      user=self.user,
                                      host=self.host)
            fclrprint(f'Connection established to {self.dbname} [{self.user}@{self.host}]', 'g')
        except psycopg2_error as e:
            print("Unable to connect to the database: %s" % str(e))
            exit(-1)

        # reset tables if requested
        if reset_tables:
            self.reset_all_tables()

    def pgcprint(self, pstr):
        ''' Debug printing method. '''

        if self.verbosity:
            fclrprint(pstr, 'b')

    def reset_all_tables(self):
        ''' Reset all tables (geom, map, contain). '''

        # construct command
        sql_reset_all_tables = sql_str_reset_all_tables(self.geom_table_name, \
                                self.map_table_name, self.contain_table_name, self.SRID)
        # get cursor
        cur = self.connection.cursor()
        # execute command
        cur.execute(sql_reset_all_tables)
        # (debug) print
        self.pgcprint(cur.query.decode())
        # commit changes
        self.connection.commit()

'''
if __name__ == "__main__":
    

    node54 = Node.from_shapefile("~/1954c.shp", meta, "1954")
    node62 = Node.from_shapefile("~/1962c.shp", meta, "1962")
    print("node 1954", node54)
    print("node 1962", node62)

    print("====test intersection====")
    new_intersect = node54.intersect(node62, "1954,1962-i")
    print("new node intersection", new_intersect)
    print("node 1954", node54)
    print("node 1962", node62)

    print("====test union====")
    new_union = node54.union(node62, "1954,1962-u")
    print("new node union", new_union)

    print("====test minus====")
    new_minus = node54.minus(node62, "1954,1962-m")
    print("new node minus", new_minus)
    print("node 1954", node54)
    print("node 1962", node62)

    print("====test error checking====")
    node54.intersect(node54)

    node62.metadata = None
    node54.intersect(node62)
'''
