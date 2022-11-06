import vnxpy

import numpy as np
from skimage.transform import downscale_local_mean
import datetime

import hornschunck as hs

class HornShunckMotionEstimator(vnxpy.Analytics1):

    def __init__(self, vv: vnxpy.Vnxvideo = None):
        super().__init__(vv)
        if 'skip' in self.config:
            self.skip = self.config['skip']
        else:
            self.skip = 4
        self.nframe = 0

    def onformat(self,colorspace,width,height):
        if colorspace >= vnxpy.EMF_AUDIO:
            return
        downscale=round(max(1,width/400,height/300))
        self.downscale=(downscale,downscale)

    prev : np.ndarray = np.zeros(0)
    downscale = (1,1)

    def onsample(self, sample : vnxpy.RawSample, timestamp):
        if not sample.is_video:
            return        
        cur = downscale_local_mean(sample.gray8().astype(float)/255.0, self.downscale)
        process = self.skip == 0 or self.nframe % (self.skip + 1) == 0
        if self.prev.size == cur.size and process:
            u, v=hs.HornSchunck(self.prev, cur, Niter=2)
            cx = sum(u.flat)/u.size
            cy = sum(v.flat)/v.size
            ts = datetime.datetime.fromtimestamp(timestamp/1000.0, tz=datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            self.event('GlobalMotionVector', {'x': cx, 'y': cy, 'timestamp': ts})
        self.prev = cur
        self.nframe = self.nframe + 1

HornShunckMotionEstimator().run()
