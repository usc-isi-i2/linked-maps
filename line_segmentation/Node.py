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
from psycopg2.extensions import AsIs
from postgis_sqls import sqlstr_reset_all_tables, sqlstr_intersect_records, \
                        sqlstr_create_gid_geom_table, sqlstr_insert_new_record_to_geom_table
from osgeo.ogr import Open as ogr_open

def verify(func):
    '''wrapper function used to verify necessary information
    before doing intersect, union etc operation. '''
    def inner(*args, **kwargs):
        if args[0].pgchannel != args[1].pgchannel:
            print("ERROR: PostGISChannel mismatch")
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
    ''' Class representing a single segment (record in 'map' table on POSTGIS BE) '''

    def __init__(self, pg_channel_obj, gid, name):
        ''' Initialize Segment. '''

        self.pgchannel = pg_channel_obj
        self.gid = gid
        self.name = name
        self.parents = dict()  # { parentname: node object }
        self.children = dict()  # { childname: node object }

    def __repr__(self):
        ''' Print string for segment class. '''

        return f'name: {self.name}, parents: {self.parents.keys()}, children: {self.children.keys()}'

    @verify
    def intersect(self, other_node, new_name, buff=0.0015):
        ''' Intersect the segment class with an additional segment. '''

        # construct command
        sql_intersect_segments = sqlstr_intersect_records(self.pgchannel.geom_table_name, self.gid, other_node.gid, buff)
        # get cursor
        cur = self.pgchannel.connection.cursor()
        # execute command
        cur.execute(sql_intersect_segments)
        # (debug) print
        self.pgchannel.pgcprint(cur.query.decode())
        # get new_gid
        new_gid = cur.fetchone()
        # create new_node
        new_node = Node(self.pgchannel, new_gid, new_name)
        # set children
        self.children[new_name] = new_node
        other_node.children[new_name] = new_node
        # set parents
        new_node.parents[self.name] = self
        new_node.parents[other_node.name] = other_node

        return new_node

    @verify
    def union(self, other_node, new_name, buff=0.0015):
        cur = self.pgchannel.connection.cursor()
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
                    (AsIs(self.pgchannel.table_name),
                     AsIs(buff),
                     AsIs(buff),
                     AsIs(self.pgchannel.table_name),
                     AsIs(self.pgchannel.table_name),
                     AsIs(self.gid),
                     AsIs(self.pgchannel.table_name),
                     AsIs(self.pgchannel.table_name),
                     AsIs(other_node.gid),
                     ))

        new_gid = cur.fetchone()
        new_node = Node(self.pgchannel, new_gid, new_name)

        # Note: Union Operation shall not result in any graph relations

        # self.children[new_name] = new_node
        # other_node.children[new_name] = new_node
        # new_node.parents[self.name] = self
        # new_node.parents[other_node.name] = other_node

        return new_node

    @verify
    def minus(self, other_node, new_name, buff=0.0015):
        cur = self.pgchannel.connection.cursor()
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
                    (AsIs(self.pgchannel.table_name),
                     AsIs(buff),
                     AsIs(buff),
                     AsIs(self.pgchannel.table_name),
                     AsIs(self.pgchannel.table_name),
                     AsIs(self.gid),
                     AsIs(self.pgchannel.table_name),
                     AsIs(self.pgchannel.table_name),
                     AsIs(other_node.gid),
                     ))

        new_gid = cur.fetchone()
        new_node = Node(self.pgchannel, new_gid, new_name)

        self.children[new_name] = new_node
        new_node.parents[self.name] = self

        # Note: New node should not be children of other_node (because of minus operation)
        # other_node.children[new_name] = new_node
        # new_node.parents[other_node.name] = other_node

        return new_node

    @classmethod
    def from_shapefile(cls, path, pg_channel_obj, name):
        ''' Create a segment class from shapefile. '''

        cur = pg_channel_obj.connection.cursor()

        working_segment_table_name = 'active_seg'
        sql_create_table = sqlstr_create_gid_geom_table(working_segment_table_name, pg_channel_obj.SRID)
        
        cur.execute(sql_create_table)
        pg_channel_obj.pgcprint(cur.query.decode())

        shapefile = ogr_open(path)
        layer = shapefile.GetLayer(0)

        sql_insert_geom_values_to_table = '''
        INSERT INTO %s (geom) VALUES (ST_MULTI(ST_GeometryFromText(%s, %s)))
        '''

        total_feature_count_in_map = layer.GetFeatureCount()
        for i in range(total_feature_count_in_map):
            feature = layer.GetFeature(i)
            wkt = feature.GetGeometryRef().ExportToWkt()
            cur.execute(sql_insert_geom_values_to_table, (AsIs(working_segment_table_name), wkt, pg_channel_obj.SRID))
        pg_channel_obj.pgcprint(f'.... Added {total_feature_count_in_map} geometry lines (records) to {working_segment_table_name}')

        sql_insert_new_segment = sqlstr_insert_new_record_to_geom_table(pg_channel_obj.geom_table_name, working_segment_table_name)
        cur.execute(sql_insert_new_segment)
        pg_channel_obj.pgcprint(cur.query.decode())

        gid = cur.fetchone()[0]
        cur.execute(f'DROP TABLE {AsIs(working_segment_table_name)}')
        pg_channel_obj.pgcprint(cur.query.decode())

        # commit changes
        pg_channel_obj.connection.commit()
        fclrprint(f'Created {name} from {path}', 'c')

        node = cls(pg_channel_obj, gid, name)
        return node


class PostGISChannel:
    ''' Class defining a PostGIS connection channel, 
    holds attributes and communication objcet for SQL (POSTGIS) transmission. '''

    def __init__(self, config_path, verbosity, reset_tables=False):
        ''' Initialize PostGISChannel. '''

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

        sql_reset_all_tables = sqlstr_reset_all_tables(self.geom_table_name, self.contain_table_name, self.SRID)
        cur = self.connection.cursor()
        cur.execute(sql_reset_all_tables)
        self.pgcprint(cur.query.decode())
        # commit changes
        self.connection.commit()
        fclrprint(f'Reset tables finished', 'c')


'''
if __name__ == "__main__":

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
