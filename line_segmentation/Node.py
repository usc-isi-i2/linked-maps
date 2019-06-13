import json

import osgeo.ogr
import psycopg2
from psycopg2.extensions import AsIs


class Node:
    def __init__(self, metadata, gid, name):
        self.metadata = metadata
        self.gid = gid
        self.name = name
        self.parent = dict()  # parentname : node object
        self.child = dict()  # childname : node object

    def __repr__(self):
        return "name : {}, parent: {}, child: {}".format(self.name, self.parent.keys(), self.child.keys())

    def intersect(self, other_node, new_name):
        if self.metadata != other_node.metadata:
            print("ERROR: Metadata Mismatched")
            return None

        if self == other_node:
            print("ERROR: Same Node")
            return None

        if self.name == other_node.name:
            print("ERROR: Same Name")
            return None

        cur = self.metadata.connection.cursor()


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


    def union(self, other_node):
        pass

    def minus(self, other_node):
        pass


    @classmethod
    def from_shapefile(cls, path, metadata, name):
        cursor = metadata.connection.cursor()
        shapefile = osgeo.ogr.Open(path)
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


class Metadata:
    def __init__(self, config_path):

        try:
            config = json.load(open(config_path, "r"))
        except Exception as e:
            print("cannot load config file, ERROR: %s" % str(e))
            exit(-1)

        try:
            self.dbname = config["dbname"]
            self.user = config["user"]
            self.host = config["host"]
            self.table_name = config["table_name"]
            self.SRID = config["SRID"]
            self.password = config["password"]
        except LookupError:
            print("invalid config JSON")
            exit(-1)

        try:
            self.connection = psycopg2.connect(dbname=self.dbname,
                                               user=self.user,
                                               host=self.host,
                                               password=self.password)
        except psycopg2.Error as e:
            print("Unable to connect to the database: %s" % str(e))
            exit(-1)


if __name__ == "__main__":
    # test
    
    config_path = r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\config2.json"
    meta = Metadata(config_path)

    node54 = Node.from_shapefile(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1954c.shp", meta, "1954")
    node62 = Node.from_shapefile(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1962c.shp", meta, "1962")

    new_node = node54.intersect(node62, "1954-1962")
    print("node 1954", node54)
    print("node 1962", node54)
    print("new node", new_node)

