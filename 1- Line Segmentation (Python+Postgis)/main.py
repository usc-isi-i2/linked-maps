from os import listdir
import psycopg2
import osgeo.ogr
from psycopg2.extensions import AsIs
from psycopg2.extras import execute_values
import sys
import time

SRID = 4269
DB_CONFIG = {
    "dbname": "test_line_segment_2",
    "user": "postgres",
    "password": "admin",
    "host": "localhost"
}

MAP_TABLE_NAME = 'maps'
SAME_AS_TABLE_NAME = 'sameas'


def create_connection():
    try:
        connection = psycopg2.connect(dbname=DB_CONFIG["dbname"], user=DB_CONFIG["user"],
                                      password=DB_CONFIG["password"], host=DB_CONFIG["host"])
        return connection
    except:
        print ("I am unable to connect to the database")


def load_shp_to_db(path):
    conn = create_connection()
    if conn:
        table_names = []
        cursor = conn.cursor()
        shapefiles = [file for file in listdir(path) if file.endswith(".shp")]
        for fname in shapefiles:
            shapefile = osgeo.ogr.Open(path + fname)
            SQL = '''
            DROP TABLE IF EXISTS %s; 
            CREATE TABLE %s (gid SERIAL NOT NULL PRIMARY KEY);
            SELECT AddGeometryColumn(%s, 'geom', %s, 'LINESTRING', 2);
            '''
            table_name = '__map' + fname.split(".")[0]
            table_names.append(table_name)
            cursor.execute(SQL, (AsIs(table_name), AsIs(table_name), table_name,  SRID,))
            layer = shapefile.GetLayer(0)
            SQL_2 = '''
            INSERT INTO %s (geom) VALUES (ST_GeometryFromText(%s, %s))
            '''
            for i in range(layer.GetFeatureCount()):
                feature = layer.GetFeature(i)
                # name = feature.GetField("NAME").decode("Latin-1")
                wkt = feature.GetGeometryRef().ExportToWkt()
                cursor.execute(SQL_2, (AsIs(table_name), wkt, SRID))

        conn.commit()
        conn.close()
        return table_names


def create_maps_table():
    conn = create_connection()
    if conn:
        CREATE_TABLE = '''
        DROP TABLE IF EXISTS %s;
        DROP TABLE IF EXISTS %s;
        create table %s (
            gid SERIAL NOT NULL PRIMARY KEY, 
            line_name  VARCHAR(256),
            isLeaf BOOL
        );
        select AddGeometryColumn(%s, 'geom', 4269, 'MULTILINESTRING', 2);
        '''

        cur = conn.cursor()
        cur.execute(CREATE_TABLE, (AsIs(SAME_AS_TABLE_NAME), AsIs(MAP_TABLE_NAME),
                                   AsIs(MAP_TABLE_NAME), MAP_TABLE_NAME))

        CREATE_SAMEAS_TABLE = '''
        DROP TABLE IF EXISTS %s;
        CREATE TABLE %s (
          gid1 INTEGER REFERENCES %s(gid),
          gid2 INTEGER REFERENCES %s(gid)
        );
    
        '''
        cur = conn.cursor()
        cur.execute(CREATE_SAMEAS_TABLE, (AsIs(SAME_AS_TABLE_NAME), AsIs(SAME_AS_TABLE_NAME),
                                          AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME)))
        conn.commit()
        conn.close()
    else:
        "ERROR"


def a_minus_b(newrol):
    conn = create_connection()
    if conn:
        SQL_DIFF = '''
            INSERT INTO %s (geom,line_name) 
            SELECT ST_INTERSECTION(
                exist.geom, 
                ST_DIFFERENCE(
                    st_buffer(exist.geom, 0.0015), 
                    st_buffer(new.geom, 0.0015)
                )
            ),exist.line_name
            FROM %s exist, %s new
            WHERE exist.isLeaf = TRUE AND
            exist.gid < %s AND
            new.gid = %s
            RETURNING gid;

        '''
        cur = conn.cursor()
        cur.execute(SQL_DIFF, (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), newrol, newrol))
        conn.commit()
        conn.close()
    else:
        print "ERROR"


def b_minus_a(newrol):
    conn = create_connection()
    if conn:
        SQL_DIFF_NEW = '''
            INSERT INTO %s (geom,line_name) 
            SELECT ST_INTERSECTION(
                new.geom, 
                ST_DIFFERENCE(
                    st_buffer(new.geom, 0.0015), 
                    st_buffer(exist.geom, 0.0015)
                )
            ),new.line_name
            FROM %s exist, %s new
            WHERE exist.isLeaf = TRUE AND
            exist.gid <%s AND
            new.gid = %s
            RETURNING gid;

        '''
        cur = conn.cursor()
        cur.execute(SQL_DIFF_NEW, (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), newrol, newrol))
        conn.commit()
        conn.close()
    else:
        print "ERROR"


def insert_and_drop(table_name):
    conn = create_connection()
    if conn:
        INSERT_NEW_MAP = '''
        INSERT INTO %s (geom, line_name, isLeaf) VALUES (
        (SELECT ST_UNION(geom) AS geom FROM %s),
        %s,
        TRUE)
        RETURNING gid;
        '''
        cur = conn.cursor()
        cur.execute(INSERT_NEW_MAP, (AsIs(MAP_TABLE_NAME), AsIs(table_name), table_name,))
        gid = cur.fetchall()
        cur.execute("DROP TABLE %s", (AsIs(table_name),))
        conn.commit()
        conn.close()
        return gid[0][0]
    else:
        print "ERROR"

def intersect_a_b(newrol):
    conn = create_connection()
    if conn:
        SQL_INTERSEC = '''
            INSERT INTO %s (geom, line_name) 
            SELECT ST_INTERSECTION(
                exist.geom, 
                ST_INTERSECTION(
                    st_buffer(exist.geom, 0.0015), 
                    st_buffer(new.geom, 0.0015)
                )
            ), exist.line_name
            FROM %s exist, %s new
            WHERE exist.isLeaf = TRUE AND
            exist.gid < %s AND
            new.gid = %s
            RETURNING gid;

        '''
        cur = conn.cursor()
        cur.execute(SQL_INTERSEC, (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), newrol, newrol))
        new_intersec_rows1 = cur.fetchall()
        conn.commit()
        conn.close()
        return new_intersec_rows1 # like [(3,)]
    else:
        print "ERROR"


def intersect_b_a(newrol):
    conn = create_connection()
    if conn:
        SQL_INTERSEC_NEW = '''
            INSERT INTO %s (geom,line_name) 
            SELECT ST_INTERSECTION(
                new.geom, 
                ST_INTERSECTION(
                    st_buffer(exist.geom, 0.0015), 
                    st_buffer(new.geom, 0.0015)
                )
            ), new.line_name
            FROM %s exist, %s new
            WHERE exist.isLeaf = TRUE AND
            exist.gid < %s AND
            new.gid = %s
            RETURNING gid;

        '''

        cur = conn.cursor()
        cur.execute(SQL_INTERSEC_NEW,
                    (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), newrol, newrol))
        new_intersec_rows2 = cur.fetchall()
        conn.commit()
        conn.close()
        return new_intersec_rows2
    else:
        print "ERROR"


#TODO cannot add same_as_1950_1988_2001 to placeholder
def update_same_as(new_intersec_rows1,new_intersec_rows2):
    assert len(new_intersec_rows1) == len(new_intersec_rows2)
    conn = create_connection()
    if conn:
        INSERT_SAMEAS = "INSERT INTO " + SAME_AS_TABLE_NAME + " (gid1,gid2) VALUES %s"
        values_list = []

        for l,r in zip(new_intersec_rows1,new_intersec_rows2):
            values_list.append((l[0], r[0]))
        cur = conn.cursor()
        execute_values(cur, INSERT_SAMEAS, values_list)
        conn.commit()
        conn.close()
    else:
        print "ERROR"


def update_leave(newrol):
    conn = create_connection()
    if conn:
        SQL_UPDATE_LEAVE = '''
        UPDATE %s 
        SET isLeaf = FALSE
        WHERE gid <= %s;
        UPDATE %s
        SET isLeaf = TRUE
        WHERE gid > %s;

        '''
        cur = conn.cursor()
        cur.execute(SQL_UPDATE_LEAVE, (AsIs(MAP_TABLE_NAME), newrol, AsIs(MAP_TABLE_NAME), newrol))
        conn.commit()
        conn.close()
    else:
        print "ERROR"

def intersect_a_b_2(newrol):
    conn = create_connection()
    if conn:
        # TODO cannot add same_as_1950_1988_2001 to placeholder
        SQL_INTERSECT_FIXED = '''
        INSERT INTO %s (line_name,geom) 
        SELECT exist.line_name,ST_MULTI(ST_INTERSECTION(
        	exist.geom, 
        	ST_INTERSECTION(
        		st_buffer(exist.geom, 0.0015), 
        		st_buffer(new.geom, 0.0015)
        	)))
        FROM 
        	%s as new, 
        	(select *
        	 from %s as m, %s as s
        	 where 
        	 	m.gid <> s.gid2 and
        	 	m.gid <%s
        	and m.isleaf = true) as exist
        WHERE
        	new.gid = %s
        RETURNING gid;



        '''

        cur = conn.cursor()
        cur.execute(SQL_INTERSECT_FIXED,
                    (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME),AsIs(SAME_AS_TABLE_NAME), newrol, newrol))
        new_intersec_rows1 = cur.fetchall()
        conn.commit()
        conn.close()
        return new_intersec_rows1 # like [(3,)]
    else:
        print "ERROR"


def intersect_b_a_2(newrol):
    conn = create_connection()
    if conn:
        # TODO cannot add same_as_1950_1988_2001 to placeholder
        SQL_INTERSEC_NEW2 = '''
        INSERT INTO %s (line_name,geom) 
        SELECT new.line_name,ST_MULTI(ST_INTERSECTION(
        	new.geom, 
        	ST_INTERSECTION(
        		st_buffer(exist.geom, 0.0015), 
        		st_buffer(new.geom, 0.0015)
        	)))
        FROM 
        	%s as new, 
        	(select *
        	 from %s as m, %s as s
        	 where 
        	 	m.gid <> s.gid2 and
        	 	m.gid <%s
        	and m.isleaf = true) as exist
        WHERE
        	new.gid = %s
        RETURNING gid;

        '''
        cur = conn.cursor()
        cur.execute(SQL_INTERSEC_NEW2,
                    (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(SAME_AS_TABLE_NAME), newrol, newrol))
        new_intersec_rows2 = cur.fetchall()
        conn.commit()
        conn.close()
        return new_intersec_rows2
    else:
        print "ERROR"


def b_minus_a_2(newrol):
    conn = create_connection()
    if conn:
        SQL_DIFF_NEW2 = '''
        INSERT INTO %s (geom,line_name) 
        SELECT ST_MULTI(ST_INTERSECTION(
        	new.geom, 
        	ST_DIFFERENCE(
        		st_buffer(new.geom, 0.0015),
        		st_buffer(exist.geom, 0.0015) 
        	))), new.line_name
        FROM 
        	%s as new, 
        	(select m.*
        	 from %s m
        	 where 
        	 	m.gid not in (select gid2 from %s) and
        	 	m.gid <%s
                and m.isleaf = true) as exist
        WHERE
        	new.gid = %s
        RETURNING gid;
        '''

        cur = conn.cursor()
        cur.execute(SQL_DIFF_NEW2, (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME),
                                    AsIs(SAME_AS_TABLE_NAME), newrol, newrol))
        conn.commit()
        conn.close()
    else:
        print "ERROR"

def a_minus_b_2(newrol):
    conn = create_connection()
    if conn:
        SQL_DIFF_NEW2 = '''
        INSERT INTO %s (geom,line_name) 
        SELECT ST_MULTI(ST_INTERSECTION(
        	exist.geom, 
        	ST_DIFFERENCE(
        		st_buffer(exist.geom, 0.0015),
        		st_buffer(new.geom, 0.0015)
        	))), exist.line_name
        FROM 
        	%s as new, 
        	(select m.*
        	 from %s m
        	 where 
        	 	m.gid not in (select gid2 from %s) and
        	 	m.gid <%s
                and m.isleaf = true) as exist
        WHERE
        	new.gid = %s
        RETURNING gid;
        '''

        cur = conn.cursor()
        cur.execute(SQL_DIFF_NEW2, (AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME), AsIs(MAP_TABLE_NAME),
                                    AsIs(SAME_AS_TABLE_NAME), newrol, newrol))

        conn.commit()
        conn.close()
    else:
        print "ERROR"


def segmentation(path):
    table_names = load_shp_to_db(path)
    create_maps_table()
    print table_names
    for i, table in enumerate(table_names):
        gid = insert_and_drop(table)
        print "gid",gid
        # first map
        if i == 0:
            continue
        elif i ==1:
            new_intersec_rows1 = intersect_a_b(gid)
            new_intersec_rows2 = intersect_b_a(gid)
            #print new_intersec_rows1, new_intersec_rows2

            a_minus_b(gid)
            b_minus_a(gid)
            update_leave(gid)
        else:
            new_intersec_rows1 = intersect_a_b_2(gid)
            new_intersec_rows2 = intersect_b_a_2(gid)
            a_minus_b_2(gid)
            b_minus_a_2(gid)

        update_same_as(new_intersec_rows1, new_intersec_rows2)
        update_leave(gid)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = r"C:\Users\Wii\Google Drive\My Doc\usc\ISI\weiwei_maps\test\\"
    print path
    start = time.time()
    segmentation(path)
    print time.time() - start

