from new_segment import Segment
from os import listdir
import sys
import time

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

segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1984c.shp", "1984", verbose=True)
segment.commit()
#
# segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\1988c.shp", "1988", verbose=True)
# segment.commit()
#
# segment.do_segment(r"C:\Users\Wii\Google Drive USC\usc\ISI\7maps_clip\clipped\2001c.shp", "2001", verbose=True)
# segment.commit()