# Automated Line Segmentation

The idea of line segmentation shall be described as follows. You can read [this paper](http://usc-isi-i2.github.io/papers/lin18.pdf) for more info.

```
    A   B
   / \ / \
  A1 A2B1 B2   
```
```
        A             B
     /     \      /        \
    A1        A2B1            B2          C
  /  \      /      \         /  \        / \ 
A11 A12C1  A21B11 A22B12C2  B21 B22C3   ..` C4
```

Algorithm
```
If we have n existing maps and will add map n+1th, 
We will have n table
Each existing n table we do
For row in leaf_nodes_row:
    insert_row_to_this_table(this_geom ∩ new_map_geom)
    insert_row_to_this_table(this_geom - new_map_geom)
Create new n+1th table, the first row is entire map
For row in leaf_nodes (linked FK):
    insert_row_to_this_table(this_geom ∩ new_map_geom)
    insert_row_to_this(new_map_geom - all existing_map)
```

**main.py**

The program shall be called as follows.

```python main.py <path/to/shapefile/>```

In our experiment, we use three maps in Bray, CA in 1950, 1988 and 2001. You will need to install PostgreSQL and Postgis and update the configuration at the top of main.py.

TODO (1/14/2019):

The program shall read the config file directly and should be called as follows;

```python main.py <path/to/shapefile/> <path/to/configure/file```
