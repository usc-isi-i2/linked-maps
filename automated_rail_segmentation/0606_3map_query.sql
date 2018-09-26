-- 4269

'''
Source Data
Shape File : Table
clip_rail13.shp : cal_rail
clip_usa.shp : usa_rail
Trans_RailFeature.shp la_rail
'''

-- create buffer intersections: this works
create table ca_la_intersections as 
	SELECT st_intersection(
        st_buffer(a.geom, 0.0001)::geometry(Polygon, 4269), 
		st_buffer(b.geom, 0.0001)::geometry(Polygon, 4269)) as geom 
	FROM 
        la_rail AS a 
        JOIN cal_rail AS b 
        ON st_dwithin(a.geom, b.geom, 0.0001);


'''
    A   B
   / \ / \
  A1 A2B1 B2   
  
A = la_rail
B = cal_rail
'''

-- create table for A1 and A2
create table la_segmented (
	gid serial, sameas varchar(80)
);

select AddGeometryColumn('la_segmented', 'geom', 4269, 'MULTILINESTRING', 2);

-- Insert line intersection A2
insert into la_segmented(geom)
select st_union(st_intersection(a.geom, b.geom)) as geom 
from la_rail as a, (
    select st_union(ca_la_intersections.geom) 
    as geom from ca_la_intersections) 
    as b
where st_intersects(a.geom, b.geom);

--insert a_diff (A1) (in A but not in A2)
insert into la_segmented(geom)
select st_difference(a.all_geom, b.all_geom) as geom 
from 
    (select st_union(geom) as all_geom from la_rail) 
    as a, 
    (select geom as all_geom 
    from la_segmented where gid = 1) 
    as b;

-- create table for B1 and B2
create table ca_segmented (
	gid serial not null,
	sameAs varchar(80)
);
select AddGeometryColumn('ca_segmented', 'geom', 4269, 'MULTILINESTRING', 2);

-- insert B1
insert into ca_segmented(geom)
select st_union(st_intersection(a.geom, b.geom)) as geom
from 
    cal_rail as a, 
    (select st_union(ca_la_intersections.geom) as geom 
    from ca_la_intersections) as b
where st_intersects(a.geom, b.geom);

-- insert B2
insert into ca_segmented(geom)
select st_difference(a.all_geom, b.all_geom) as geom 
from 
    (select st_union(geom) as all_geom from cal_rail) 
    as a, 
    (select geom as all_geom from ca_segmented where gid = 1) 
    as b;

'''

TABLE la_segmented

gid   sameas  geom
1              A2 (B1)
2              A1

TABLE ca_segmented
gid   sameas  geom
1              B1 (A2)
2              B2

'''    
    
-- Add usa_rail

'''
        A             B
     /     \      /        \
    A1        A2B1            B2          C
  /  \      /      \         /  \        / \ 
A11 A12C1  A21B11 A22B12C2  B21 B22C3   ..` C4

A = la_rail
B = cal_rail
C = usa_rail
'''

create table usa_segmented (
	gid serial, sameAs varchar(80));
select AddGeometryColumn ('usa_segmented', 'geom', 4269, 'MULTILINESTRING', 2);

insert into usa_segmented (geom)
select st_union(geom) as geom
from usa_rail;
---A22B12C2
--C2
insert into usa_segmented (geom)
select st_intersection(
        c.geom, 
        st_intersection(
            st_union(
                st_buffer(a.geom, 0.0015), 
                st_buffer(b.geom, 0.0015)), 
                st_buffer(c.geom, 0.0015)))
from la_segmented a, ca_segmented b, usa_segmented c
where a.gid = 1 and b.gid = 1 and c.gid = 1;

'''
TABLE usa_segmented
gid   sameas  geom
1              C (all)
2              C2 (A22 and B12)
'''

--A22
insert into la_segmented (geom)
select st_intersection(
        a.geom, 
        st_intersection(
            st_union(
                st_buffer(a.geom, 0.0015), 
                st_buffer(b.geom, 0.0015)), 
                st_buffer(c.geom, 0.0015)))
from la_segmented a, ca_segmented b, usa_segmented c
where a.gid = 1 and b.gid = 1 and c.gid = 1;

'''
TABLE la_segmented

gid   sameas  geom
1              A2 (B1)
2              A1
3              A22 (C2 and B12)

'''

--B12
insert into ca_segmented (geom)
select st_intersection(
        b.geom, 
        st_intersection(
            st_union(
                st_buffer(a.geom, 0.0015), 
                st_buffer(b.geom, 0.0015)), 
                st_buffer(c.geom, 0.0015)))
from la_segmented a, ca_segmented b, usa_segmented c
where a.gid = 1 and b.gid = 1 and c.gid = 1;

'''
TABLE ca_segmented

gid   sameas  geom
1              B1 (A2)
2              B2
3              B12 (C2 and A22)

'''

-- A12C1
--C1 
insert into usa_segmented (geom)
select st_intersection(
        c.geom, 
        st_intersection(
            st_buffer(a.geom, 0.0015), 
            st_buffer(c.geom, 0.0015)))
from la_segmented a, usa_segmented c
where a.gid = 2 and c.gid = 1;
'''
TABLE usa_segmented
gid   sameas  geom
1              C (all)
2              C2 (A22 and B12)
3              C1  (sameAs A12)
'''

--A12
insert into la_segmented (geom)
select st_intersection(
        a.geom, 
        st_intersection(
            st_buffer(a.geom, 0.0015), 
            st_buffer(c.geom, 0.0015)))
from la_segmented a, usa_segmented c
where a.gid = 2 and c.gid = 1;
'''
TABLE la_segmented

gid   sameas  geom
1              A2 (B1)
2              A1
3              A22 (C2 and B12)
4              A12 (sameAs C1)
'''

--B22C3
--C3
insert into usa_segmented (geom)
select st_intersection(
        c.geom, 
        st_intersection(
            st_buffer(b.geom, 0.0015), 
            st_buffer(c.geom, 0.0015)))
from ca_segmented b, usa_segmented c
where b.gid = 2 and c.gid = 1;
'''
TABLE usa_segmented
gid   sameas  geom
1              C (all)
2              C2 (A22 and B12)
3              C1 (sameAs A12)
4              C3 (sameAs B22)
'''

--B22
insert into ca_segmented (geom)
select st_intersection(
        b.geom, 
        st_intersection(
            st_buffer(b.geom, 0.0015), 
            st_buffer(c.geom, 0.0015)))
from ca_segmented b, usa_segmented c
where b.gid = 2 and c.gid = 1;
'''
TABLE ca_segmented

gid   sameas  geom
1              B1 (A2)
2              B2
3              B12 (C2 and A22)
4              B22 (sameAs C3)

'''

--C4
insert into usa_segmented (geom)
select st_difference(c.geom, st_union(array[abc.geom, ac.geom, bc.geom])) 
from
    (select geom from usa_segmented where gid = 1) as c,
    (select st_intersection(
		st_union(
            st_buffer(a.geom, 0.0015), 
            st_buffer(b.geom, 0.0015)), 
        st_buffer(c.geom, 0.0015)) as geom
    from la_segmented a, ca_segmented b, usa_segmented c
    where a.gid = 1 and b.gid = 1 and c.gid = 1) as abc,
    (select st_intersection(
		st_buffer(a.geom, 0.0015), 
		st_buffer(c.geom, 0.0015)) as geom
    from la_segmented a, usa_segmented c
    where a.gid = 2 and c.gid = 1) as ac,
    (select st_intersection(
		st_buffer(b.geom, 0.0015), 
		st_buffer(c.geom, 0.0015)) as geom
    from ca_segmented b, usa_segmented c
    where b.gid = 2 and c.gid = 1) as bc;
'''
TABLE usa_segmented
gid   sameas  geom
1              C (all)
2              C2 (A22 and B12)
3              C1 (sameAs A12)
4              C3 (sameAs B22)
5              C4 
'''

--A11
insert into la_segmented (geom)
select st_difference(a.geom, st_intersection(
		st_union(
            st_buffer(a.geom, 0.0015), 
            st_buffer(b.geom, 0.0015)), 
        st_buffer(c.geom, 0.0015)))
from la_segmented a, ca_segmented b, usa_segmented c
where a.gid = 1 and b.gid = 1 and c.gid = 1;
'''
TABLE la_segmented

gid   sameas  geom
1              A2 (B1)
2              A1
3              A22 (C2 and B12)
4              A12 (sameAs C1)
5              A11
'''

--A21
insert into la_segmented (geom)
select st_difference(a.geom, st_intersection(
		st_buffer(a.geom, 0.0015), 
		st_buffer(c.geom, 0.0015)))
from la_segmented a, usa_segmented c
where a.gid = 2 and c.gid = 1;
'''
TABLE la_segmented

gid   sameas  geom
1              A2 (B1)
2              A1
3              A22 (C2 and B12)
4              A12 (sameAs C1)
5              A11
6              A21
'''

--B21
insert into ca_segmented (geom)
select st_difference(
        b.geom, 
        st_intersection(
            st_union(
                st_buffer(a.geom, 0.0015), 
                st_buffer(b.geom, 0.0015)), 
            st_buffer(c.geom, 0.0015)))
from la_segmented a, ca_segmented b, usa_segmented c
where a.gid = 1 and b.gid = 1 and c.gid = 1;
'''
TABLE ca_segmented

gid   sameas  geom
1              B1 (A2)
2              B2
3              B12 (C2 and A22)
4              B22 (sameAs C3)
5              B21

'''
--B11
insert into ca_segmented (geom)
select st_difference(
        b.geom, 
        st_intersection(
            st_buffer(b.geom, 0.0015), 
            st_buffer(c.geom, 0.0015)))
from ca_segmented b, usa_segmented c
where b.gid = 2 and c.gid = 1;
'''
TABLE ca_segmented

gid   sameas  geom
1              B1 (A2)
2              B2
3              B12 (C2 and A22)
4              B22 (sameAs C3)
5              B21
6              B11

'''