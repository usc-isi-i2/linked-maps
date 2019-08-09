from psycopg2.extensions import AsIs

def sqlstr_reset_all_tables(geom_tablename, contain_tablename, srid):
    ''' Get SQL string to drop all tables (geom, map, contain). '''

    sql_str = f'''
        DROP TABLE IF EXISTS {AsIs(geom_tablename)};
        DROP TABLE IF EXISTS {AsIs(contain_tablename)};
        create table {AsIs(geom_tablename)} (
            gid SERIAL NOT NULL PRIMARY KEY,
            wkt VARCHAR
        );
        select AddGeometryColumn('{AsIs(geom_tablename)}', 'geom', {srid}, 'MULTILINESTRING', 2);
        create table {AsIs(contain_tablename)} (
            par_id INTEGER,
            child_id INTEGER
        );
        '''
    return sql_str

def sqlstr_op_records(operation, geom_tablename, segment_1_gid, segment_2_gid, buffer_size):
    ''' Get SQL string to perform operation 'op' between two records . '''
    
    sql_str = f'''
        INSERT INTO {AsIs(geom_tablename)} (wkt, geom) 
        SELECT ST_ASTEXT(res.lr), lr
        FROM(
            SELECT ST_MULTI(ST_INTERSECTION(
                l.geom, 
                {operation}(
                    st_buffer(l.geom, {buffer_size}), 
                    st_buffer(r.geom, {buffer_size}))         
            )) as lr
            FROM 
                (
                SELECT geom
                FROM {AsIs(geom_tablename)}
                WHERE {AsIs(geom_tablename)}.gid = {segment_1_gid}
                ) as l,
                (
                SELECT geom
                FROM {AsIs(geom_tablename)}
                WHERE {AsIs(geom_tablename)}.gid = {segment_2_gid}
                ) as r
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
