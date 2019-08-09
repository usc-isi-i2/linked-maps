from psycopg2.extensions import AsIs

def sql_str_reset_all_tables(geom_tablename, map_tablename, contain_tablename, srid):
    ''' Get SQL string to drop all tables (geom, map, contain). '''

    sql_str = f'''
        DROP TABLE IF EXISTS {AsIs(map_tablename)};
        DROP TABLE IF EXISTS {AsIs(geom_tablename)};
        DROP TABLE IF EXISTS {AsIs(contain_tablename)};
        create table {AsIs(map_tablename)} (
            id SERIAL NOT NULL PRIMARY KEY, 
            line_name  VARCHAR(256),
            gid INTEGER,
            isLeaf BOOL
        );
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