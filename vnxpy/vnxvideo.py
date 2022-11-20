from ctypes import *
import os
import numpy as np
import traceback

def _checkReturn(code, name):
    if code!=0:
        raise Exception('{0} failed with code {1}'.format(name,code))

class Vnxvideo:
    __vnxdll = None

    def __init__(self, libpath=None):
        if libpath==None:
            if os.name=='nt':
                libpath = os.environ['PROGRAMFILES']+"\\Viinex\\bin\\vnxvideo.dll"
            else:
                libpath = '/usr/lib/libvnxvideo.so'
        self.__vnxdll=cdll.LoadLibrary(libpath)
        x=self.__vnxdll.vnxvideo_init(None,None,None)
        _checkReturn(x,'vnxvideo_init')

    def local_client(self, objname, onFormat, onRawSample):
        return LocalClient(self.__vnxdll, objname, onFormat, onRawSample)

    def local_server(self, objname, apertureMB):
        return LocalServer(self.__vnxdll, objname, apertureMB)


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
        try:
            with RawSample(self.__vnxdll, sample) as s:
                self.__userOnRawSample(s, ts)
        except:
            traceback.print_exc()
        return 0
    def __onFormat(self, emf, p, q):
        try:
            self.__userOnFormat(emf, p, q)
        except:
            traceback.print_exc()
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

class LocalServer:
    __vnxdll = None
    __pserver = None
    __allocator = None
    __last_exception = None

    __last_format = None

    def __init__(self, vnxdll, objname, aperture):
        self.__vnxdll = vnxdll
        self.__pserver = c_void_p(None)
        self.__allocator = c_void_p(None)
        action = self.CB_ACTION(lambda usrptr: self.__do_init(objname, aperture))
        x = self.__vnxdll.vnxvideo_with_shm_allocator_str(c_char_p(objname.encode()), c_int(aperture), action, c_void_p(None))
        _checkReturn(x, "vnxvideo_with_shm_allocator_str failed")
        if self.__last_exception != None:
            e = self.__last_exception
            self.__last_exception = None
            raise e

    def __do_init(self, objname, aperture):
        try:
            x=self.__vnxdll.vnxvideo_local_server_create(c_char_p(objname.encode()), c_int(aperture), byref(self.__pserver))
            _checkReturn(x, "vnxvideo_local_server_create")
            self.__vnxdll.vnxvideo_shm_allocator_duplicate(byref(self.__allocator))
        except BaseException as e:
            self.__last_exception = e

    def close(self):
        if self.__pserver.value != None:
            self.__vnxdll.vnxvideo_rawproc_free(self.__pserver)
            self.__pserver = c_void_p(None)
            self.__vnxdll.vnxvideo_shm_allocator_free(self.__allocator)
            self.__allocator = c_void_p(None)

    def __enter__(self):
        return self
    def __exit__(self, exct, excn, tb):
        self.close()
    def __del__(self):
        self.close()

    def __check_format(self, w, h):
        if self.__pserver.value == None:
            raise Exception('local server is not in open state')
        if (w, h) != self.__last_format:
            x = self.__vnxdll.vnxvideo_rawproc_set_format(self.__pserver, c_int(1), c_int(w), c_int(h))
            _checkReturn(x, 'vnxvideo_rawproc_set_format')
            self.__last_format = (w, h)

    CB_ACTION = CFUNCTYPE(None, c_void_p)

    def publish_rgb(self, img, timestamp):
        h, w, _ = img.shape
        self.__check_format(w, h)
        action = self.CB_ACTION(lambda usrptr: self.__do_publish(img, timestamp))
        x = self.__vnxdll.vnxvideo_with_shm_allocator_ptr(self.__allocator, action, None)
        _checkReturn(x, 'vnxvideo_with_shm_allocator_ptr')
        if self.__last_exception != None:
            e = self.__last_exception
            self.__last_exception = None
            raise e
        

    def __do_publish(self, img, timestamp):
        sample = c_void_p(None)
        try:
            w, h = self.__last_format
            x = self.__vnxdll.vnxvideo_raw_sample_allocate(c_int(1), c_int(w), c_int(h), byref(sample))
            _checkReturn(x, "vnxvideo_raw_sample_allocate")

            strides = STRIDES4(0,0,0,0)
            planes = PLANES4(None,None,None,None)
            x = self.__vnxdll.vnxvideo_raw_sample_get_data(sample, strides, planes)
            _checkReturn(x, "vnxvideo_raw_sample_get_data")

            y, u, v = rgb2yuv(img)
            copy_planar_data_u8(planes[0], strides[0], y)
            copy_planar_data_u8(planes[1], strides[1], u)
            copy_planar_data_u8(planes[2], strides[2], v)

            x = self.__vnxdll.vnxvideo_rawproc_process(self.__pserver, sample, c_uint64(timestamp))
            _checkReturn(x, "vnxvideo_raw_rawproc_process")
        except BaseException as e:
            self.__last_exception = e
        finally:
            self.__vnxdll.vnxvideo_raw_sample_free(sample)
            
        
def copy_planar_data_u8(plane, stride, src):
    """
    Copies the data of 2-dimensional numpy array 'src' into a raw memory buffer
    starting at 'plane' (pointer) and having the pitch value of 'stride'.
    """
    (h, w) = src.shape
    if src.__array_interface__['strides'] != None:
        raise Exception('non-null strides not supported')
    if w > stride:
        raise Exception('source width is larger than destination stride')
    s = src.__array_interface__['data'][0]
    d = cast(plane, c_void_p).value
    for y in range(0, h):
        memmove(d, s, w)
        s = s + w
        d = d + stride


STRIDES4 = c_int * 4
PLANES4 = POINTER(c_uint8) * 4

EMF_NONE = 0
EMF_I420 = 1
EMF_NV12 = 3
EMF_AUDIO   = 31
EMF_LPCM16  = 32 # S16 packed
# formats below are given for reference only.
# viinex renderer should convert audio to singed int16 packed
EMF_LPCM32  = 33 # S32 packed
EMF_LPCMF   = 34 # float packed
EMF_LPCM16P = 35 # S16 planar
EMF_LPCM32P = 36 # S32 planar
EMF_LPCMFP  = 37 # float planar


class RawSample:
    __vnxdll : c_void_p
    __sample : c_void_p
    __strides : STRIDES4
    __planes : PLANES4
    __p : c_int
    __q : c_int
    __emf : c_int

    def __init__(self, vnxdll, sample):
        self.__vnxdll=vnxdll
        self.__sample = c_void_p(None)
        self.__strides = STRIDES4(0,0,0,0)
        self.__planes = PLANES4(None,None,None,None)
        self.__p=c_int(0)
        self.__q=c_int(0)
        self.__emf=c_int(0)
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
        if self.__emf.value != EMF_NONE:
            return
        x=self.__vnxdll.vnxvideo_raw_sample_get_format(self.__sample, byref(self.__emf), byref(self.__p), byref(self.__q))
        _checkReturn(x,'vnxvideo_raw_sample_get_format')
        if self.__emf.value != EMF_I420 and self.__emf.value != EMF_NV12 and self.__emf.value < EMF_AUDIO:
            raise Exception("Viinex frame formats other than YUV420 planar and NV12 are not supported here")
        x=self.__vnxdll.vnxvideo_raw_sample_get_data(self.__sample, self.__strides, self.__planes)
        _checkReturn(x,'vnxvideo_raw_sample_get_data')

    @property
    def format(self):
        self._get_data()
        return self.__emf.value

    @property
    def p(self):
        self._get_data()
        return self.__p.value

    @property
    def q(self):
        self._get_data()
        return self.__q.value

    @property
    def width(self):
        self._get_data()
        if self.__emf.value < EMF_AUDIO:
            return self.__p.value
        else:
            raise Exception("This is not a video frame")

    @property
    def height(self):
        self._get_data()
        if self.__emf.value < EMF_AUDIO:
            return self.__q.value
        else:
            raise Exception("This is not a video frame")

    @property
    def nb_samples(self):
        self._get_data()
        if self.__emf.value > EMF_AUDIO:
            return self.__p.value
        else:
            raise Exception("This is not an audio frame")

    @property
    def channels(self):
        self._get_data()
        if self.__emf.value > EMF_AUDIO:
            return self.__q.value
        else:
            raise Exception("This is not an audio frame")

    @property
    def is_audio(self):
        return self.format >= EMF_AUDIO

    @property
    def is_video(self):
        return self.format < EMF_AUDIO

    def gray8(self):
        self._get_data()
        if self.__emf.value > EMF_AUDIO:
            raise Exception("This is not a video frame")
        y = np.ctypeslib.as_array(self.__planes[0], (self.__q.value, self.__strides[0]))
        if self.__p.value == self.__strides[0]:
            return y
        else:
            return y[:, 0:(self.__p.value-1)]

    def yuv(self):
        self._get_data()
        if self.__emf.value > EMF_AUDIO:
            raise Exception("This is not a video frame")
        y = np.ctypeslib.as_array(self.__planes[0], (self.__q.value, self.__strides[0]))
        if self.__p.value != self.__strides[0]:
            y = y[:, 0:(self.__p.value-1)]

        if self.__emf.value == EMF_I420:
            w2 = round(self.__p.value / 2)
            h2 = round(self.__q.value / 2)
            u = np.ctypeslib.as_array(self.__planes[1], (h2, self.__strides[1]))
            if self.__strides[1] != w2:
                u = u[:, 0:(w2 - 1)]
            v = np.ctypeslib.as_array(self.__planes[2], (h2, self.__strides[2]))
            if self.__strides[2] != w2:
                v = v[:, 0:(w2 - 1)]
        if self.__emf.value == EMF_NV12:
            uv = np.ctypeslib.as_array(self.__planes[1], (self.__q.value, self.__strides[1]))
            u = uv[:, 0:2:]
            v = uv[:, 1:2:]
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

    def lpcm_s16(self):
        self._get_data()
        if self.__emf.value != EMF_LPCM16:
            raise Exception("This is not an LPCM S16 audio frame")
        plane = cast(self.__planes[0], POINTER(c_int16))
        # return each channel data as a separate row in resulting numpy matrix.
        # packed format of input is equivalent to "Fortran" element order
        # (channels innermost, i.e. columns of the matrix that we want to return),
        # so we need to transpose it to get what we want.
        # resulting matrix shape is (channels, nb_samples)
        v = np.ctypeslib.as_array(plane, (self.nb_samples, self.channels)).T
        return v


def yuv2rgb(yuv):
    m = np.array([
            [1.164,  1.164, 1.164],
            [0.000, -0.392, 2.017],
            [1.596, -0.813, 0.000],
        ])

    yuv = yuv.astype(float)

    yuv[:,:, 0] = yuv[:,:, 0].clip(16.0, 235.0) - 16.0
    yuv[:,:,1:] = yuv[:,:,1:].clip(16.0, 240.0) - 128.0

    yuv = yuv / 255.0

    rgb = np.dot(yuv, m).clip(0.0, 1.0)

    return rgb

def rgb2yuv(rgb):
    m = np.array([[0.098, 0.504, 0.257],
                  [0.439, -0.291, -0.148],
                  [-0.071, -0.368, 0.439]]).T
    
    yuv = np.dot(rgb.astype(np.float), m)
    
    y = (yuv[:,:,0] + 16.0).clip(16.0, 235.0).astype(np.uint8, order='C')
    u = (yuv[::2, ::2, 1] + 128.0).clip(16.0, 240.0).astype(np.uint8, order='C')
    v = (yuv[::2, ::2, 2] + 128.0).clip(16.0, 240.0).astype(np.uint8, order='C')

    return y, u, v
