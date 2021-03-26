import vnxpy
import numpy as np
import cv2

def onformat(colorspace,width,height):
    print("onformat", colorspace, width, height)

def onsample(sample, timestamp):
    #cv2.imshow('vnxpy view',sample.rgb24())
    cv2.imshow('vnxpy view',sample.rgb24().astype(float))

cv2.imshow("vnxpy view", np.zeros([600,800]))

vv = vnxpy.Vnxvideo()

with vv.local_client("rend0", onformat, onsample) as c:
    c.start()
    cv2.waitKey()
    c.stop()
