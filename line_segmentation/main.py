from argparse import ArgumentParser
from os import listdir
from os.path import basename
from mykgutils import fclrprint
from Node import PostGISChannel, Node

# --- entrypoint --------------------------------------------------------------

def main():

    ap = ArgumentParser(description=f'Process shapefiles (vector data) and generate (csv) tables with line segmentation info.\n\tUSAGE: python {basename(__file__)} -d DIR_NAME')
    ap.add_argument('-d', '--dir_name', help='Directory path with shapefiles.', type=str)
    ap.add_argument('-c', '--config_file', help='Input configuration file.', type=str)
    ap.add_argument('-v', '--debug_prints', help='Print additional debug prints.', default=False, action='store_true')
    ap.add_argument('-r', '--reset_db', help='Reset Databases prior to processing.', default=False, action='store_true')
    args = ap.parse_args()

    if args.dir_name and args.config_file:
        fclrprint(f'Going to process shapefiles in dir {args.dir_name} using configurations from file {args.config_file}...')
        process_shapefiles(args.dir_name, args.config_file, args.debug_prints, args.reset_db)
    else:
        fclrprint(f'Input directory and configuration file were not provided.', 'r')
        exit(1)

def process_shapefiles(directory_path, configuration_file, verbosity_on, reset_database):
    ''' Generate csv tables from shapefile in a given directory,
    use given configurations to interact with POSTGRESQL to execute POSTGIS actions. '''

    channel_inst = PostGISChannel(configuration_file, verbosity_on, reset_database)
    source_nodes = list()
    for fname in listdir(directory_path):
        if fname.endswith(".shp"):
            fname_no_ext = fname.split('.shp')[0]
            full_fname = directory_path + '/' + fname
            fclrprint(f'Processing {full_fname}', 'c')
            try:
                node = Node.from_shapefile(full_fname, channel_inst, fname_no_ext)
                fclrprint(f'created node from shapefile {full_fname}: {node}', 'c')
                source_nodes.append(node)
            except Exception as e:
                fclrprint(f'Failed processing file {full_fname}\n{str(e)}', 'r')
                exit(-1)
            # TODO: sub: segment.sql_commit()
    '''
    # testing....
    fclrprint(f'Finshed creating source_nodes: {source_nodes}', 'p')
    nd0 = source_nodes[0]
    nd1 = source_nodes[1]

    fclrprint(f'Testing intersection between {nd0.name} (nd0) and {nd1.name} (nd1)', 'p')
    ndint = nd0.intersect(nd1, f'i_{nd0.name}_{nd1.name}')
    fclrprint(f'created ndint {ndint.name}: {ndint}', 'p')
    fclrprint(f'modified nd0 {nd0.name}: {nd0}', 'p')
    fclrprint(f'modified nd1 {nd1.name}: {nd1}', 'p')
    channel_inst.connection.commit()

    fclrprint(f'Testing minus between {nd0.name} (nd0) and {ndint.name} (ndint)', 'p')
    nd0_min_ndint = nd0.minus(ndint, f'm_{nd0.name}_{ndint.name}')
    fclrprint(f'created nd0_min_ndint {nd0_min_ndint.name}: {nd0_min_ndint}', 'p')
    fclrprint(f'modified nd0 {nd0.name}: {nd0}', 'p')
    fclrprint(f'modified nd1 {nd1.name}: {nd1}', 'p')
    channel_inst.connection.commit()

    fclrprint(f'Testing minus between {nd1.name} (nd1) and {ndint.name} (ndint)', 'p')
    nd1_min_ndint = nd1.minus(ndint, f'm_{nd1.name}_{ndint.name}')
    fclrprint(f'created nd1_min_ndint {nd1_min_ndint.name}: {nd1_min_ndint}', 'p')
    fclrprint(f'modified nd0 {nd0.name}: {nd0}', 'p')
    fclrprint(f'modified nd1 {nd1.name}: {nd1}', 'p')
    channel_inst.connection.commit()
    '''

    fclrprint('Segmentation finished!', 'g')

if __name__ == '__main__':
    main()
        