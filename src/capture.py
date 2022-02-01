#!/usr/bin/env python
"""Simple Python script to capture images from a webcam.

Uses the OpenCV libray via its cv2 interface, see:
http://opencv.willowgarage.com/wiki/

Tested under Mac OS X 10.7 "Lion", but should work under
Linux and Windows as well.
"""
import sys
import time
import itertools
from optparse import OptionParser
try:
    import cv #TODO - Where do the property constants live in cv2?
    import cv2
except ImportError:
    sys.stderr.write("Please install OpenCV and the cv and cv2 Python interfaces\n")
    sys.exit(1)

parser = OptionParser(add_help_option=False, usage="""Capture series for webcam frames.

For example, for 10 frames at 1280x960 named 'New Moon--DATE--TIME.png', use:
-n 10 -w 1280 -h 960 -m "New Moon"
""")
parser.add_option("-?", "--help",
                  action="help",
                  help="Show help")
parser.add_option("-m", "--name",
                  help="Filename prefix")
parser.add_option("-n", "--number", type="int",
                  help="Number of frames (default is infinite, -1 means live)")
parser.add_option("-p", "--pause", type="float",
                  help="Pause in seconds between frames (default is none)")
parser.add_option("-f", "--frame", action="store_true",
                  help="Name files with frame number suffix (default is time-stamp)")
parser.add_option("-h", "--height", type="int",
                  help="Resolution height in pixels")
parser.add_option("-w", "--width", type="int",
                  help="Resolution width in pixels")
parser.add_option("-d", "--device", type="int", default=0,
                  help="Which camera device?")
parser.add_option("-v", "--verbose", action="store_true",
                  help="Verbose output (debug)")
(options, args) = parser.parse_args()

def get_resolution(video_capture):
    return video_capture.get(cv.CV_CAP_PROP_FRAME_WIDTH), \
           video_capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT)

def set_resolution(video_capture, width, height):
    video_capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, width)
    video_capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, height)
    w, h = get_resolution(video_capture)
    assert (width, height) == (w, h), \
        "Failed to set resolution to %i x %i, got %i x %i" \
        % (width, height, w, h)
    return width, height

def debug(video_capture):
    for prop, name in [
        (cv.CV_CAP_PROP_MODE, "Mode"),
        (cv.CV_CAP_PROP_BRIGHTNESS, "Brightness"),
        (cv.CV_CAP_PROP_CONTRAST, "Contrast"),
        (cv.CV_CAP_PROP_SATURATION, "Saturation"),
        (cv.CV_CAP_PROP_HUE, "Hue"),
        (cv.CV_CAP_PROP_GAIN, "Gain"),
        (cv.CV_CAP_PROP_EXPOSURE, "Exposure"),
        ]:
        value = video_capture.get(prop)
        if value == 0:
            print " - %s not available" % name
        else:
            print " - %s = %r" % (name, value)


if options.number < 0:
    template = "LIVE.png"
    print "Will write to LIVE file only"
elif options.frame:
    template = "%05i.png"
else:
    template = "%s.png" #time-stamp
if options.name:
    template = options.name.replace("%","%%") + "--" + template

vidcap = cv2.VideoCapture()
assert vidcap.open(options.device)
if options.verbose:
    debug(vidcap)

if options.width and options.height:
    set_resolution(vidcap, options.width, options.height)
elif options.width or options.height:
    sys.stderr("Must supply height AND width (or neither)\n")
    sys.exit(1)
w, h = get_resolution(vidcap)

if options.number > 0:
    frames = xrange(options.number)
else:
    frames = itertools.count()
if options.verbose:
    print "Starting..."
start = time.time()
for f in frames:
    retval, image = vidcap.read()
    if options.number < 0:
        filename = template #LIVE, i.e. replace in situ
    elif options.frame:
        filename = template % f
    else:
        now_sec = time.time()
        now = time.gmtime(now_sec)
        now_str = "%04i-%02i-%02i--%02i-%02i-%02i" % now[:6]
        #Want sub-second accuracy...
        now_str += ".%02i" % int(100*(now_sec - int(now_sec)))
        filename = template % now_str
    assert retval, retval
    assert image is not None, image
    assert w, h == image.size
    assert cv2.imwrite(filename, image)
    if options.verbose:
        print "%s - frame %i" % (filename, f)
    if options.pause > 0:
        time.sleep(options.pause)
print "Approx %0.1ffps" % (float(f) / (time.time()-start))
if options.verbose:
    print "Done"
    debug(vidcap)
vidcap.release()
sys.exit(0)
