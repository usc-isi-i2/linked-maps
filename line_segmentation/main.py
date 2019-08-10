from argparse import ArgumentParser
from os import listdir
from os.path import basename
from mykgutils import fclrprint
from time import time
from datetime import timedelta
from segment import PostGISChannel, Segment
from json import dumps
from collections import OrderedDict 

# --- entrypoint --------------------------------------------------------------

def main():

    ap = ArgumentParser(description=f'Process shapefiles (vector data) and generate (jl) files with line segmentation info.\n\tUSAGE: python {basename(__file__)} -d DIR_NAME -c CONFIG_FILE')
    ap.add_argument('-d', '--dir_name', help='Directory path with shapefiles.', type=str)
    ap.add_argument('-c', '--config_file', help='Input configuration file.', type=str)
    ap.add_argument('-o', '--output_file', help='Output geometry file (jl).', default='line_seg.jl', type=str)
    ap.add_argument('-v', '--debug_prints', help='Print additional debug prints.', default=False, action='store_true')
    ap.add_argument('-r', '--reset_db', help='Reset Databases prior to processing.', default=False, action='store_true')
    args = ap.parse_args()

    if args.dir_name and args.config_file:
        fclrprint(f'Going to process shapefiles in dir {args.dir_name} using configurations from file {args.config_file}...')
        process_shapefiles(args.dir_name, args.config_file, args.output_file, args.debug_prints, args.reset_db)
    else:
        fclrprint(f'Input directory and configuration file were not provided.', 'r')
        exit(1)

class SegmentsGraph:
    ''' Class representing the segments graph. '''

    def __init__(self, pg_channel_object):
        ''' Initialize graph. '''

        self.pgchannel = pg_channel_object
        self.sg = list()

    def __repr__(self):
        ''' Print segments in graph. '''

        repr_str = ''
        for seg in self.sg:
            repr_str += str(seg) + '\n'
        return repr_str

    def export_geom_jl_file(self, geom_outputfile):
        ''' Export geometry mapping file to json-lines file '''

        self.pgchannel.export_geom_table_to_file(geom_outputfile)

    def export_segments_jl_file(self, seg_outputfile):
        ''' Export segments list to json-lines file '''

        with open(seg_outputfile, 'w') as write_file:
            for seg in self.sg:
                line_dict = OrderedDict()
                line_dict['gid'] = seg.gid
                line_dict['name'] = seg.name
                seg_yrs = list()
                # TODO: mapping from name to year should be read from an external file
                if '_' not in seg.name:
                    seg_yrs.append(seg.name[0:4])
                line_dict['years'] = seg_yrs

                write_file.write(dumps(line_dict) + '\n')
        fclrprint(f'Exported segments info to file {seg_outputfile}', 'c')

    def export_relations_jl_file(self, rel_outputfile):
        ''' Export relations list to json-lines file '''

        with open(rel_outputfile, 'w') as write_file:
            for seg in self.sg:
                for child_gid in seg.children.keys():
                    line_dict = OrderedDict()
                    line_dict['parent_gid'] = seg.gid
                    line_dict['child_gid'] = child_gid
                    write_file.write(dumps(line_dict) + '\n')
        fclrprint(f'Exported realtions info to file {rel_outputfile}', 'c')

    def add_segment_to_graph(self, segment):
        ''' Add segment to the graph. '''

        leaves = self.get_leaf_nodes()

        # append new segment to graph
        self.sg.append(segment)

        list_of_leaf_gids = list()
        for leaf_seg in leaves:
            # intersect
            int_seg = leaf_seg.intersect(segment, f'i_{leaf_seg.name}_{segment.name}')
            if int_seg:
                fclrprint(f'[{int_seg.gid}] = [{leaf_seg.gid}] ∩ [{segment.gid}]', 'p')
                self.sg.append(int_seg)
                list_of_leaf_gids.append(int_seg.gid)
            # leaf    minus intersection
            leaf_min_int = leaf_seg.minus(int_seg, f'm_{leaf_seg.name}_{int_seg.name}')
            if leaf_min_int:
                fclrprint(f'[{leaf_min_int.gid}] = [{leaf_seg.gid}] \\ [{int_seg.gid}]', 'p')
                self.sg.append(leaf_min_int)

        if list_of_leaf_gids:
            # segment minus union-of-intersections
            segment_min_union_ints = segment.minus_union_of_segments(list_of_leaf_gids, f'mu_{segment.name}_UL')
            if segment_min_union_ints:
                fclrprint(f'[{segment_min_union_ints.gid}] = [{segment.gid}] \\ ∪∊{list_of_leaf_gids}', 'p')
                self.sg.append(segment_min_union_ints)
        
        # commit changes
        self.pgchannel.connection.commit()
        
    def get_leaf_nodes(self):
        ''' Get leaf nodes in graph. '''

        list_of_leaf_nodes = list()
        for seg in self.sg:
            if len(seg.children) == 0:
                list_of_leaf_nodes.append(seg)
                fclrprint(f'leaf [{seg}]', 'p')
        return list_of_leaf_nodes

def process_shapefiles(directory_path, configuration_file, outputfile, verbosity_on, reset_database):
    ''' Generate csv tables from shapefile in a given directory,
    use given configurations to interact with POSTGRESQL to execute POSTGIS actions. '''

    channel_inst = PostGISChannel(configuration_file, verbosity_on, reset_database)
    sgraph = SegmentsGraph(channel_inst)
    
    start_time = time()
    for fname in listdir(directory_path):
        if fname.endswith(".shp"):
            fname_no_ext = fname.split('.shp')[0]
            full_fname = directory_path + '/' + fname
            fclrprint(f'Processing {full_fname}', 'c')
            try:
                seg = Segment.from_shapefile(full_fname, channel_inst, fname_no_ext)
                sgraph.add_segment_to_graph(seg)
            except Exception as e:
                fclrprint(f'Failed processing file {full_fname}\n{str(e)}', 'r')
                exit(-1)
            fclrprint(f'Took {str(timedelta(seconds=int(time() - start_time))).zfill(8)}', 'c')
    
    print(sgraph)
    fclrprint('Segmentation finished!', 'g')
    sgraph.export_geom_jl_file(outputfile.replace('.jl', '.geom.jl'))
    sgraph.export_segments_jl_file(outputfile.replace('.jl', '.seg.jl'))
    sgraph.export_relations_jl_file(outputfile.replace('.jl', '.rel.jl'))

if __name__ == '__main__':
    main()
        
