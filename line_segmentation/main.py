from new_segment import Segment
from os import listdir
import sys

if __name__ == "__main__":

    if len(sys.argv) == 3:
        path_to_shp     = sys.argv[1]
        path_to_config  = sys.argv[2]
        print("Path to config file: %s" % path_to_config)
        print("Path to shape files: %s" % path_to_shp)
        segment = Segment(path_to_config, is_reset = True)
        for fname in listdir(path_to_shp):
            if fname.split(".")[-1] == "shp":
                fname_no_ext = fname.split(".")[0]
                full_fname = path_to_shp + '/' + fname
                print("Performing segmentation on %s" % full_fname)
                try:
                    segment.do_segment(full_fname, fname_no_ext, True)
                except Exception as e:
                    print("failed segmenting file %s\n%s" % (full_fname, str(e)))
                    exit(-1)
                segment.sql_commit()
        print("Segmentation done!")

    else:
        print("invalid command")
        exit(-1)