# -*- coding: utf-8 -*-

"""
This class is a part of the line segmentation algorithm.
This Segment class is abstraction of segments (nodes) in segmentation tree.
Each segment contains its name, PostGISChannel object, and a "pointer" pointed the geometric it represents.
Also, since it is a node in graph, it will contain its parents and children.
"""

from mykgutils import fclrprint
from json import load
from psycopg2 import connect, Error as psycopg2_error
from psycopg2.extensions import AsIs
from postgis_sqls import OPERATION_DIFF_W_UNION, OPERATION_INTERSECT, OPERATION_UNION, OPERATION_MINUS, \
                        sqlstr_reset_all_tables, sqlstr_op_records, \
                        sqlstr_create_gid_geom_table, sqlstr_insert_new_record_to_geom_table, \
                        sqlstr_export_geom_table_to_file
from osgeo.ogr import Open as ogr_open

def verify(func):
    '''wrapper function used to verify necessary information
    before doing intersect, union etc operation. '''
    def inner(*args, **kwargs):
        if args[0].pgchannel != args[1].pgchannel:
            print("ERROR: PostGISChannel mismatch")
            return None

        if args[0] == args[1]:
            print("ERROR: Same Segment")
            return None

        if args[0].name == args[1].name:
            print("ERROR: Same Name")
            return None
        return func(*args, **kwargs)

    return inner


class Segment:
    ''' Class representing a single segment (record in 'map' table on POSTGIS BE) '''

    def __init__(self, pg_channel_obj, gid, name):
        ''' Initialize Segment. '''

        self.pgchannel = pg_channel_obj
        self.gid = gid
        self.name = name
        self.parents = dict()  # { parentgid: Segment object }
        self.children = dict()  # { childgid: Segment object }

    def __repr__(self):
        ''' Print string for segment class. '''

        return 'name: %s, gid: %s, parents: %s, children: %s' \
        % (self.name, self.gid, str(self.parents.keys()), str(self.children.keys()))

    def perform_sql_op(self, list_of_other_gids, new_name, operation, buff=0.0015):
        ''' Performs an operation on the segment class with an additional segment,
        supported operations: OPERATION_INTERSECT, OPERATION_UNION, OPERATION_MINUS '''

        sql_op_segments = sqlstr_op_records(operation, self.pgchannel.geom_table_name, self.gid, list_of_other_gids, buff)
        cur = self.pgchannel.connection.cursor()
        cur.execute(sql_op_segments)
        self.pgchannel.pgcprint(cur.query.decode())
        fetchall = cur.fetchall()
        print('fetchall: %s' % (fetchall))
        if len(fetchall) > 1:
            raise ValueError("Fetched too many entries (should be 0 or 1)")
        try:
            new_gid = fetchall[0][0]
            new_seg = Segment(self.pgchannel, new_gid, new_name)
            return new_seg
        except:
            pass

        return None

    @verify
    def intersect(self, other_seg, new_name, buff=0.0015):
        ''' Intersect the segment class with an additional segment. '''

        new_seg = self.perform_sql_op([other_seg.gid], new_name, OPERATION_INTERSECT, buff)

        if new_seg:
            # set children
            self.children[new_seg.gid] = new_seg
            other_seg.children[new_seg.gid] = new_seg
            # set parents
            new_seg.parents[self.gid] = self
            new_seg.parents[other_seg.gid] = other_seg
        return new_seg

    @verify
    def union(self, other_seg, new_name, buff=0.0015):
        ''' Union the segment class with an additional segment. '''

        new_seg = self.perform_sql_op([other_seg.gid], new_name, OPERATION_UNION, buff)
        return new_seg

    @verify
    def minus(self, other_seg, new_name, buff=0.0015):
        ''' Minus the segment class with an additional segment. '''

        new_seg = self.perform_sql_op([other_seg.gid], new_name, OPERATION_MINUS, buff)

        if new_seg:
            self.children[new_seg.gid] = new_seg
            new_seg.parents[self.gid] = self
        return new_seg

    def minus_union_of_segments(self, list_of_other_segs, new_name, buff=0.0015):
        ''' Minus the segment class with a list of additional segments. '''

        new_seg = self.perform_sql_op(list_of_other_segs, new_name, OPERATION_DIFF_W_UNION, buff)

        if new_seg:
            self.children[new_seg.gid] = new_seg
            new_seg.parents[self.gid] = self
        return new_seg


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
        pg_channel_obj.pgcprint('.... Added %s geometry lines (records) to %s' \
                                % (total_feature_count_in_map, working_segment_table_name))

        sql_insert_new_segment = sqlstr_insert_new_record_to_geom_table(pg_channel_obj.geom_table_name, working_segment_table_name)
        cur.execute(sql_insert_new_segment)
        pg_channel_obj.pgcprint(cur.query.decode())

        fetchall = cur.fetchall()
        print('fetchall: %s' % (fetchall))
        if len(fetchall) != 1:
            raise ValueError("Fetched zero or more entries (should be exactly 1)")
        gid = fetchall[0][0]

        cur.execute('DROP TABLE %s' % (AsIs(working_segment_table_name)))
        pg_channel_obj.pgcprint(cur.query.decode())

        # commit changes
        pg_channel_obj.connection.commit()
        fclrprint('Created %s from %s' % (name, path), 'c')

        seg = cls(pg_channel_obj, gid, name)
        return seg


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
            self.SRID               = config["SRID"]
        except LookupError:
            print("Invalid configuration file")
            exit(-1)

        # establish connection
        try:
            self.connection = connect(dbname=self.dbname,
                                      user=self.user,
                                      host=self.host)
            fclrprint('Connection established to %s [%s@%s]'
                      % (self.dbname, self.user, self.host), 'g')
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

        sql_reset_all_tables = sqlstr_reset_all_tables(self.geom_table_name, self.SRID)
        cur = self.connection.cursor()
        cur.execute(sql_reset_all_tables)
        self.pgcprint(cur.query.decode())
        # commit changes
        self.connection.commit()
        fclrprint('Reset tables finished', 'c')

    def export_geom_table_to_file(self, geometry_output_jl):
        ''' Export the geometry file to some json-lines file. '''

        export_sql = sqlstr_export_geom_table_to_file(self.geom_table_name, geometry_output_jl)
        cur = self.connection.cursor()
        cur.execute(export_sql)
        self.pgcprint(cur.query.decode())
        # commit changes
        self.connection.commit()
        fclrprint('Exported geomtery info to file %s' % (geometry_output_jl), 'c')

