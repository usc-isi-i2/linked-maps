
    A   B
   / \ / \
  A1 A2B1 B2   
  

        A             B
     /     \      /        \
    A1        A2B1            B2          C
  /  \      /      \         /  \        / \ 
A11 A12C1  A21B11 A22B12C2  B21 B22C3   ..` C4

Algorithm
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
