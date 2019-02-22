from new_segment import Segment
from os import listdir
import sys
import time


if __name__ == "__main__":

    if len(sys.argv) == 2 and sys.argv[1] == '-m':
        '''
        Write your own instruction here. 
        '''

        ##########################################
        #### Your code start here ################
        ##########################################

        start = time.time()
        path_to_config = r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\config.json"
        segment = Segment(path_to_config, is_reset=False)

        # segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1950c.shp", "1950", verbose=True)
        # segment.commit()
        #
        # segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1954c.shp", "1954", verbose=True)
        # segment.commit()

        # segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1958c.shp", "1958", verbose=True)
        # segment.commit()

        # segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1962c.shp", "1962", verbose=True)
        # segment.commit()

        segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1984c.shp", "1984",
                           verbose=True)
        segment.commit()
        #
        # segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1988c.shp", "1988", verbose=True)
        # segment.commit()
        #
        # segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\2001c.shp", "2001", verbose=True)
        # segment.commit()

        ##########################################
        #### End of your code ####################
        ##########################################

    elif len(sys.argv) == 4 and sys.argv[1] == '-a':
        path_to_shp = sys.argv[2]
        path_to_config = sys.argv[3]
        print "path to config file: ", path_to_config
        print "path to shape files: ", path_to_shp
        segment = Segment(path_to_config, is_reset=True)
        for fname in listdir(path_to_shp):
            if fname.split(".")[-1] == "shp":
                print "perform segmentation on {}".format(fname)
                try:
                    segment.do_segment(path_to_shp + '\\' + fname, fname.split(".")[0])
                except Exception  as e:
                    print "failed segmenting on {}".format(fname)
                    print e
                    exit(-1)

                segment.commit()
        print "Done!"

    else:
        print "invalid command"
        exit(-1)

