from argparse import ArgumentParser
from os import listdir
from os.path import basename
from mykgutils import fclrprint
from Node import PostGISChannel

'''
TODO: remove
from new_segment import Segment
'''

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

    config_md_inst = PostGISChannel(configuration_file, verbosity_on, reset_database)
    # TODO: sub: segment = Segment(path_to_config, is_reset = True)
    for fname in listdir(directory_path):
        if fname.endswith(".shp"):
            fname_no_ext = fname.split('.shp')[0]
            full_fname = directory_path + '/' + fname
            fclrprint(f'Processing {full_fname}', 'c')
            try:
                fclrprint(f'segment.do_segment()', 'c')
                # TODO: sub: segment.do_segment(full_fname, fname_no_ext, True)
            except Exception as e:
                fclrprint(f'Failed processing file {full_fname}\n{str(e)}', 'r')
                exit(-1)
            # TODO: sub: segment.sql_commit()
    fclrprint('Segmentation finished!', 'g')

if __name__ == '__main__':
    main()
        