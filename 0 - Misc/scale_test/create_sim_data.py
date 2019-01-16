# vector schema
## sameas,gid,WKT,URI,map

import random
import string

vector_size = 60000
sim_vec = ''.join(['1' for i in range(vector_size)])

vec_file = open('a.csv','w')
vec_file.write('sameas,gid,WKT,URI,map\n')

con_file = open('contain.csv','w')
con_file.write('id,contains\n')

mapa_name = 'clip_usa'
mapb_name = 'usgs_trans'

uriset = set()


def main():
    # args: number of map, number of vectors in each map, vector size, tree depth, ...

    map_a_num = 5000
    map_b_num = 5000
    inter_num = 2500

    gen_vectors(map_a_num,map_b_num,inter_num)

def gen_vectors(map_a_num,map_b_num,inter_num):

    vector_cnt = 0

    a_ids = gen_id_list(map_a_num)
    b_ids = gen_id_list(map_b_num)
    
    
    

    child_a_not_inter = gen_id_list(inter_num)
    child_a_inter = gen_id_list(inter_num)
    child_b_not_inter = gen_id_list(inter_num)
    child_b_inter = gen_id_list(inter_num)

    for i in a_ids + child_a_not_inter:
        vec_file.write(',{},{},{},{}\n'.format(str(vector_cnt),sim_vec,i,mapa_name))
        vector_cnt += 1
    
    for i in b_ids + child_b_not_inter:
        vec_file.write(',{},{},{},{}\n'.format(str(vector_cnt),sim_vec,i,mapb_name))
        vector_cnt += 1

    for idx,i in enumerate(child_a_inter):
        vec_file.write('{},{},{},{},{}\n'.format(child_b_inter[idx],str(vector_cnt),sim_vec,i,mapa_name))
        vector_cnt += 1

    for idx,i in enumerate(child_b_inter):
        vec_file.write('{},{},{},{},{}\n'.format(child_a_inter[idx],str(vector_cnt),sim_vec,i,mapb_name))
        vector_cnt += 1

    gen_contains(a_ids,child_a_inter)
    gen_contains(a_ids,child_a_not_inter)
    gen_contains(b_ids,child_b_inter)
    gen_contains(b_ids,child_b_not_inter)

def gen_id_list(num):
    a_ids = []
    for i in range(num):
        tmp = gen_random_uri()
        while tmp in uriset:
            tmp = gen_random_uri()
        uriset.add(tmp)
        a_ids.append(tmp)
    return a_ids     

def gen_contains(a_ids,child_ids):
    
    for i in range(len(child_ids)):
        con_file.write('{},{}\n'.format(a_ids[i],child_ids[i]))
    

def gen_random_uri():
    return ''.join(random.sample(string.letters + string.digits, 8))


if __name__ == "__main__":
    main()