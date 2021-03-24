import vnxvideo
import extproc

import numpy as np
from skimage.transform import downscale_local_mean
#import cv2
import json
import sys
import fileinput

import hornschunck as hs

#vv = vnxvideo.Vnxvideo()

class HornShunckMotionEstimator(extproc.Analytics1):

    def onformat(self,colorspace,width,height):
        downscale=round(max(1,width/400,height/300))
        self.downscale=(downscale,downscale)

    prev : np.ndarray = np.zeros(0)
    downscale = (1,1)

    def onsample(self, sample : vnxvideo.RawSample, timestamp):
        cur = downscale_local_mean(sample.gray8().astype(float)/255.0, self.downscale)
        if self.prev.size == cur.size:
            u, v=hs.HornSchunck(self.prev, cur, Niter=2)
            cx = sum(u.flat)/u.size
            cy = sum(v.flat)/v.size
            self.event('GlobalMotionVector', {'x': cx, 'y': cy, 'timestamp': timestamp})
            #self.prev.free()
            #print("free")
        self.prev = cur # sample.dup()
        #print("dup")
        #cv2.imshow('pppp',cur)

    # @property
    # def video_source(self):
    #     return "rend0"

#cv2.imshow("pppp", np.random.randn(600,800))
HornShunckMotionEstimator().run()


# cfgs = sys.stdin.readline()
# print(cfgs)
# cfg = json.loads(cfgs)
# print(cfg)

# with vv.local_client("rend0", hse.onformat, hse.onsample) as c:
# #    cv2.waitKey()
#     c.start()
# #    cv2.waitKey()
#     for line in fileinput.input():
#         pass