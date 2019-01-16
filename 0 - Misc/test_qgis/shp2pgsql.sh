shp2pgsql -I -s 4326 test_line.shp public.test_line | psql -U postgres -d test_qgis
shp2pgsql -I -s 4326 altered.shp public.altered | psql -U postgres -d test_qgis
# -d: database name
# public.test_line: table name
# -s: srid, Spatial Reference System Identifier
# -I: Create a GiST index on the geometry column

# http://www.bostongis.com/pgsql2shp_shp2pgsql_quickguide.bqg
