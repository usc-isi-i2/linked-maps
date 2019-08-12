from os.path import abspath
from psycopg2.extensions import AsIs

OPERATION_INTERSECT = 'ST_INTERSECTION'
OPERATION_UNION = 'ST_UNION'
OPERATION_MINUS = 'ST_DIFFERENCE'
OPERATION_DIFF_W_UNION = 'INTERNAL_DIFF_W_UNION'

def sqlstr_reset_all_tables(geom_tablename, srid):
    ''' Get SQL string to reset tables (geom). '''

    sql_str = f'''
        DROP TABLE IF EXISTS {AsIs(geom_tablename)};
        create table {AsIs(geom_tablename)} (
            gid SERIAL NOT NULL PRIMARY KEY,
            wkt VARCHAR
        );
        select AddGeometryColumn('{AsIs(geom_tablename)}', 'geom', {srid}, 'MULTILINESTRING', 2);
        '''
    return sql_str

def sqlstr_op_records(operation, geom_tablename, segment_1_gid, list_of_gids, buffer_size):
    ''' Get SQL string to perform operation 'op' between two records . '''

    sub_op = operation
    if operation == OPERATION_DIFF_W_UNION:
        sub_op = OPERATION_MINUS

    sql_str = f'''
        INSERT INTO {AsIs(geom_tablename)} (wkt, geom)
        SELECT ST_ASTEXT(res.lr), lr
        FROM(
            SELECT ST_MULTI(
                ST_INTERSECTION(
                    l.geom,
                    {sub_op}(
                        st_buffer(l.geom, {buffer_size}),
                        st_buffer(r.geom, {buffer_size})
                    )
                )
            ) as lr
            FROM (
                SELECT geom
                FROM {AsIs(geom_tablename)}
                WHERE {AsIs(geom_tablename)}.gid = {segment_1_gid}
            ) as l,
        '''

    gid_2_sql_substring = sqlstr_build_or_clause_of_gids(geom_tablename, list_of_gids)

    if operation == OPERATION_DIFF_W_UNION:
        sql_str += f'''
            (
                SELECT ST_Multi(ST_Union(f.geom)) as geom
                FROM (
                    SELECT geom
                    FROM {AsIs(geom_tablename)}
                    WHERE {gid_2_sql_substring}
                ) as f
            ) as r
        '''
    else:
        sql_str += f'''
            (
                SELECT geom
                FROM {AsIs(geom_tablename)}
                WHERE {gid_2_sql_substring}
            ) as r
        '''

    sql_str += f'''
        ) res
        where ST_geometrytype(res.lr) = 'ST_MultiLineString'
        RETURNING gid
        '''

    return sql_str

def sqlstr_create_gid_geom_table(active_tablename, srid):
    ''' Create a table with gid, geom data. '''

    sql_str = f'''
        DROP TABLE IF EXISTS {AsIs(active_tablename)}; 
        CREATE TABLE {AsIs(active_tablename)} (gid SERIAL NOT NULL PRIMARY KEY);
        SELECT AddGeometryColumn('{AsIs(active_tablename)}', 'geom', {srid}, 'MULTILINESTRING', 2);
        '''
    return sql_str

def sqlstr_insert_new_record_to_geom_table(geom_tablename, active_tablename):
    ''' Create a table with gid, geom data. '''

    sql_str = f'''
        INSERT INTO {AsIs(geom_tablename)} (wkt, geom)
            SELECT ST_ASTEXT(ST_UNION(geom)), ST_UNION(geom)
            FROM {AsIs(active_tablename)}
            RETURNING gid;
        '''
    return sql_str

def sqlstr_build_or_clause_of_gids(geom_tablename, list_of_gids):
    ''' Union (clause) of gids from a list of gid/gids. '''

    sql_substr = f""
    for gid_idx, gid_val in enumerate(list_of_gids):
        if gid_idx > 0:
            sql_substr += f' or'
        sql_substr +=  f' {AsIs(geom_tablename)}.gid = {gid_val}'
    return sql_substr

def sqlstr_export_geom_table_to_file(geom_tablename, jl_filename):
    ''' Get SQL commaind for exporting the geometry file to some json-lines file. '''

    sql_str = f'''
        COPY (SELECT ROW_TO_JSON(t) FROM (SELECT * FROM {AsIs(geom_tablename)}) t) TO '{abspath(jl_filename)}'
        '''
    return sql_str
