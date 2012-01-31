#!/usr/bin/env python
"""Simple Python script to capture images from a webcam.

Uses the OpenCV libray via its cv2 interface, see:
http://opencv.willowgarage.com/wiki/

Tested under Mac OS X 10.7 "Lion", but should work under
Linux and Windows as well.
"""
import sys
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
    assert (width, height) == get_resolution(video_capture), \
        "Failed to set resoution to %i x %i" % (width, height)
    return width, height

vidcap = cv2.VideoCapture()
assert vidcap.open(0)
retval, image = vidcap.retrieve()
assert retval, retval
assert image is not None, image
w, h = get_resolution(vidcap)
assert w, h == image.size
assert cv2.imwrite("test_%ix%i.png" % (w, h), image)

print "Trying to change resolution..."
w, h = set_resolution(vidcap, 640, 480)
retval, image = vidcap.retrieve()
assert retval, retval
assert image is not None, image
assert cv2.imwrite("test_%ix%i.png" % (w, h), image)

vidcap.release()
print "Done"
