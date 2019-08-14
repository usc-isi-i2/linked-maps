from os.path import abspath
from psycopg2.extensions import AsIs

OPERATION_INTERSECT = 'ST_INTERSECTION'
OPERATION_UNION = 'ST_UNION'
OPERATION_MINUS = 'ST_DIFFERENCE'
OPERATION_DIFF_W_UNION = 'INTERNAL_DIFF_W_UNION'

def sqlstr_reset_all_tables(geom_tablename, srid):
    ''' Get SQL string to reset tables (geom). '''

    sql_str = '''
        DROP TABLE IF EXISTS %s;
        create table %s (
            gid SERIAL NOT NULL PRIMARY KEY,
            wkt VARCHAR
        );
        select AddGeometryColumn('%s', 'geom', %s, 'MULTILINESTRING', 2);
        ''' % (AsIs(geom_tablename), AsIs(geom_tablename), AsIs(geom_tablename), srid)
    return sql_str

def sqlstr_op_records(operation, geom_tablename, segment_1_gid, list_of_gids, buffer_size):
    ''' Get SQL string to perform operation 'op' between two records . '''

    sub_op = operation
    if operation == OPERATION_DIFF_W_UNION:
        sub_op = OPERATION_MINUS

    sql_str = '''
        INSERT INTO %s (wkt, geom)
        SELECT ST_ASTEXT(res.lr), lr
        FROM(
            SELECT ST_MULTI(
                ST_INTERSECTION(
                    l.geom,
                    %s(
                        st_buffer(l.geom, %s),
                        st_buffer(r.geom, %s)
                    )
                )
            ) as lr
            FROM (
                SELECT geom
                FROM %s
                WHERE %s.gid = %s
            ) as l,
        ''' % (AsIs(geom_tablename), sub_op, buffer_size, buffer_size, \
               AsIs(geom_tablename), AsIs(geom_tablename), segment_1_gid)

    gid_2_sql_substring = sqlstr_build_or_clause_of_gids(geom_tablename, list_of_gids)

    if operation == OPERATION_DIFF_W_UNION:
        sql_str += '''
            (
                SELECT ST_Multi(ST_Union(f.geom)) as geom
                FROM (
                    SELECT geom
                    FROM %s
                    WHERE %s
                ) as f
            ) as r
        ''' % (AsIs(geom_tablename), gid_2_sql_substring)
    else:
        sql_str += '''
            (
                SELECT geom
                FROM %s
                WHERE %s
            ) as r
        ''' % (AsIs(geom_tablename), gid_2_sql_substring)

    sql_str += '''
        ) res
        where ST_geometrytype(res.lr) = 'ST_MultiLineString'
        RETURNING gid
        '''

    return sql_str

def sqlstr_create_gid_geom_table(active_tablename, srid):
    ''' Create a table with gid, geom data. '''

    sql_str = '''
        DROP TABLE IF EXISTS %s; 
        CREATE TABLE %s (gid SERIAL NOT NULL PRIMARY KEY);
        SELECT AddGeometryColumn('%s', 'geom', %s, 'MULTILINESTRING', 2);
        ''' % (AsIs(active_tablename), AsIs(active_tablename), AsIs(active_tablename), srid)
    return sql_str

def sqlstr_insert_new_record_to_geom_table(geom_tablename, active_tablename):
    ''' Create a table with gid, geom data. '''

    sql_str = '''
        INSERT INTO %s (wkt, geom)
            SELECT ST_ASTEXT(ST_UNION(geom)), ST_UNION(geom)
            FROM %s
            RETURNING gid;
        ''' % (AsIs(geom_tablename), AsIs(active_tablename))
    return sql_str

def sqlstr_build_or_clause_of_gids(geom_tablename, list_of_gids):
    ''' Union (clause) of gids from a list of gid/gids. '''

    sql_substr = ""
    for gid_idx, gid_val in enumerate(list_of_gids):
        if gid_idx > 0:
            sql_substr += ' or'
        sql_substr +=  ' %s.gid = %s' % (AsIs(geom_tablename), gid_val)
    return sql_substr

def sqlstr_export_geom_table_to_file(geom_tablename, jl_filename):
    ''' Get SQL commaind for exporting the geometry file to some json-lines file. '''

    sql_str = '''
        COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM %s) t) TO '%s'
        ''' % (AsIs(geom_tablename), abspath(jl_filename))
    return sql_str
