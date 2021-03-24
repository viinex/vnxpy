from ctypes import *
import os
import numpy as np

def _checkReturn(code, name):
    if code!=0:
        raise name+' failed with code '+code

class Vnxvideo:
    __vnxdll = None

    def __init__(self, libpath=None):
        if libpath==None:
            if os.name=='nt':
                libpath = os.environ['PROGRAMFILES']+"\\Viinex\\bin\\vnxvideo.dll"
            else:
                libpath = '/usr/lib/vnxvideo.so'
        self.__vnxdll=cdll.LoadLibrary(libpath)
        x=self.__vnxdll.vnxvideo_init(None,None,None)
        _checkReturn(x,'vnxvideo_init')

    def local_client(self, objname, onFormat, onRawSample):
        return LocalClient(self.__vnxdll, objname, onFormat, onRawSample)


class LocalClient:
    __vnxdll = None
    __pclient = None

    CB_ON_FORMAT=CFUNCTYPE(c_int, c_void_p, c_int, c_int, c_int)
    CB_ON_RAW_SAMPLE=CFUNCTYPE(c_int, c_void_p, c_void_p, c_int64)

    __cb_on_format = None
    __cb_on_sample = None
    __userOnRawSample = None
    __userOnFormat = None

    def __init__(self, vnxdll, objname, onFormat, onRawSample):
        self.__vnxdll=vnxdll
        self.__pclient=c_void_p(None)
        x=self.__vnxdll.vnxvideo_local_client_create(c_char_p(objname.encode()), byref(self.__pclient))
        _checkReturn(x,'vnxvideo_local_client_create')
        self.__userOnRawSample=onRawSample
        self.__userOnFormat=onFormat
        self.__cb_on_format = self.CB_ON_FORMAT(lambda usrptr, csp, w, h: self.__onFormat(csp,w,h))
        self.__cb_on_sample = self.CB_ON_RAW_SAMPLE(lambda usrptr, sample, ts: self.__onRawSample(sample,ts))
        x=self.__vnxdll.vnxvideo_video_source_subscribe(self.__pclient, self.__cb_on_format, c_void_p(None), self.__cb_on_sample, c_void_p(None))
        _checkReturn(x,'vnxvideo_video_source_subscribe')

    def __onRawSample(self, sample, ts):
        with RawSample(self.__vnxdll, sample) as s:
            self.__userOnRawSample(s, ts)
        return 0
    def __onFormat(self, csp, w, h):
        self.__userOnFormat(csp, w, h)
        return 0

    def start(self):
        x=self.__vnxdll.vnxvideo_video_source_start(self.__pclient)
        _checkReturn(x,'vnxvideo_video_source_start')

    def stop(self):
        x=self.__vnxdll.vnxvideo_video_source_stop(self.__pclient)
        _checkReturn(x,'vnxvideo_video_source_stop')

    def close(self):
        if self.__pclient.value != None:
            self.stop()
            x=self.__vnxdll.vnxvideo_video_source_subscribe(self.__pclient, c_void_p(None), c_void_p(None), c_void_p(None), c_void_p(None))
            _checkReturn(x,'vnxvideo_video_source_subscribe')
        self.__vnxdll.vnxvideo_video_source_free(self.__pclient)
        self.__pclient=c_void_p(None)

    def __enter__(self):
        return self
    def __exit__(self, exct, excn, tb):
        self.close()
    def __del__(self):
        self.close()

STRIDES4 = c_int * 4
PLANES4 = POINTER(c_uint8) * 4

class RawSample:
    __vnxdll : c_void_p
    __sample : c_void_p
    __strides : STRIDES4
    __planes : PLANES4
    __w : c_int
    __h : c_int
    __csp : c_int

    def __init__(self, vnxdll, sample):
        self.__vnxdll=vnxdll
        self.__sample = c_void_p(None)
        self.__strides = STRIDES4(0,0,0,0)
        self.__planes = PLANES4(None,None,None,None)
        self.__w=c_int(0)
        self.__h=c_int(0)
        self.__csp=c_int(0)
        x=self.__vnxdll.vnxvideo_raw_sample_dup(c_void_p(sample), byref(self.__sample))
        _checkReturn(x,'vnxvideo_raw_sample_dup')

    def free(self):
        self.__vnxdll.vnxvideo_raw_sample_free(self.__sample)
        self.__sample=c_void_p(None)
    def dup(self):
        return RawSample(self.__vnxdll, self.__sample.value)
    def __enter__(self):
        return self
    def __exit__(self, exct, excn, tb):
        self.free()
    def __del__(self):
        self.free()
    def _get_data(self):
        if self.__csp.value != 0:
            return
        x=self.__vnxdll.vnxvideo_raw_sample_get_format(self.__sample, byref(self.__csp), byref(self.__w), byref(self.__h))
        _checkReturn(x,'vnxvideo_raw_sample_get_format')
        if self.__csp.value != 1:
            raise "Viinex frame formats other than YUV420 planar not supported here"
        x=self.__vnxdll.vnxvideo_raw_sample_get_data(self.__sample, self.__strides, self.__planes)
        _checkReturn(x,'vnxvideo_raw_sample_get_data')

    def gray8(self):
        self._get_data()
        y = np.ctypeslib.as_array(self.__planes[0], (self.__h.value, self.__strides[0]))
        if self.__w.value == self.__strides[0]:
            return y
        else:
            return y[:, 0:(self.__w.value-1)]

    def yuv(self):
        self._get_data()
        y = np.ctypeslib.as_array(self.__planes[0], (self.__h.value, self.__strides[0]))
        if self.__w.value != self.__strides[0]:
            y = y[:, 0:(self.__w.value-1)]
        w2 = round(self.__w.value / 2)
        h2 = round(self.__h.value / 2)
        u = np.ctypeslib.as_array(self.__planes[1], (h2, self.__strides[1]))
        if self.__strides[1] != w2:
            u = u[:, 0:(w2 - 1)]
        v = np.ctypeslib.as_array(self.__planes[2], (h2, self.__strides[2]))
        if self.__strides[2] != w2:
            v = v[:, 0:(w2 - 1)]
        return y,u,v

    def rgb24(self):
        y,u,v = self.yuv()
        u = np.repeat(u, 2, axis = 1)
        u = np.repeat(u, 2, axis = 0)
        v = np.repeat(v, 2, axis = 1)
        v = np.repeat(v, 2, axis = 0)
        y  = y.reshape((y.shape[0], y.shape[1], 1))
        u  = u.reshape((u.shape[0], u.shape[1], 1))
        v  = v.reshape((v.shape[0], v.shape[1], 1))        
        yuv = np.concatenate((y, v, u), axis=2)
        return yuv2rgb(yuv) #np.dstack([y,u,v])/255.0

def yuv2rgb(yuv):
    # not quite accurate transform, but not sure how to figure out the proper matrix
    # m = np.array([
    #         [1.000,  1.000, 1.000],
    #         [0.000, -0.394, 2.032],
    #         [1.130, -0.581, 0.000],
    #     ])    
    # m = np.array([
    #         [1.164,  1.164, 1.164],
    #         [0.000, -0.392, 2.017],
    #         [1.596, -0.813, 0.000],
    #     ])    
    m = np.array([
            [1.000,  1.000, 1.000],
            [0.000, -0.344, 1.772],
            [1.402, -0.714, 0.000],
        ])    

    yuv = yuv.astype(float) / 255.0
    yuv[:, :, 0] -= 0.0625
    yuv[:, :, 1:] -= 0.5
    rgb = np.dot(yuv, m)
    return rgb