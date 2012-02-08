#!/usr/bin/env python
"""Simple Python script to capture images from a webcam.

Uses the OpenCV libray via its cv2 interface, see:
http://opencv.willowgarage.com/wiki/

Tested under Mac OS X 10.7 "Lion", but should work under
Linux and Windows as well.
"""
import sys
import time
try:
    import cv #TODO - Where do the property constants live in cv2?
    import cv2
except ImportError:
    sys.stderr.write("Please install OpenCV and the cv and cv2 Python interfaces\n")
    sys.exit(1)

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


def capture_batch(video_capture, frames, name):
    start = time.time()
    for frame in xrange(frames):
        retval, image = vidcap.read()
        assert retval, retval
        assert image is not None, image
        assert cv2.imwrite(name % frame, image)
    print "%i frames, approx %0.1f fps" \
          % (frames, frames / (time.time()-start))

vidcap = cv2.VideoCapture()
assert vidcap.open(1)
retval, image = vidcap.retrieve()
assert retval, retval
assert image is not None, image
w, h = get_resolution(vidcap)
assert w, h == image.size
assert cv2.imwrite("test_%ix%i.png" % (w, h), image)
debug(vidcap)
#Seeing about 7fps at default 1280x960 resolution of
#Xbox Live Vision camera
capture_batch(vidcap, 50, "test_%ix%i_f%%03i.png" % (w,h))

print "Trying to change resolution..."
w, h = set_resolution(vidcap, 640, 480)
retval, image = vidcap.retrieve()
assert retval, retval
assert image is not None, image
assert cv2.imwrite("test_%ix%i.png" % (w, h), image)
debug(vidcap)
#Seeing about 15fps at 640x480 resolution for Xbox Live Vision
capture_batch(vidcap, 100, "test_%ix%i_f%%03i.png" % (w,h))

print "Trying to change gain..."
vidcap.set(cv.CV_CAP_PROP_GAIN, 0)
retval, image = vidcap.retrieve()
assert retval, retval
assert image is not None, image
assert cv2.imwrite("test_%ix%i_gain.png" % (w, h), image)
debug(vidcap)

vidcap.release()
print "Done"
