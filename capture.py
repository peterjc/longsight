#!/usr/bin/env python
"""Simple Python script to capture images from a webcam.

Uses the OpenCV libray via its cv2 interface, see:
http://opencv.willowgarage.com/wiki/

Tested under Mac OS X 10.7 "Lion", but should work under
Linux and Windows as well.
"""
import sys
try:
    import cv2
except ImportError:
    sys.stderr.write("Please install OpenCV and its cv2 Python interface\n")
    sys.exit(1)


vidcap = cv2.VideoCapture()
assert vidcap.open(0)
retval, image = vidcap.retrieve()
assert retval, retval
assert image is not None, image
vidcap.release()
assert cv2.imwrite("test.png", image)

print "Done"
