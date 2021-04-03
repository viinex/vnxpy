import sys
import json
import fileinput

from .vnxvideo import *

class Logging:
    @staticmethod
    def __log(prefix='I', *args, **kwargs):
        print(prefix, *args, file=sys.stderr, flush=True, **kwargs)

    @staticmethod
    def log(*args, **kwargs):
        Logging.__log('I', *args, **kwargs)

    @staticmethod
    def info(*args, **kwargs):
        Logging.__log('I', *args, **kwargs)

    @staticmethod
    def debug(*args, **kwargs):
        Logging.__log('D', *args, **kwargs)

    @staticmethod
    def warning(*args, **kwargs):
        Logging.__log('W', *args, **kwargs)

    @staticmethod
    def error(*args, **kwargs):
        Logging.__log('E', *args, **kwargs)

class ExtProc:
    """
    A class implementing the skeleton of a module.
    """
    __config: object

    def __init__(self):
        cfgs = sys.stdin.readline()
        self.__config = json.loads(cfgs)

    @staticmethod
    def event(topic, data): # following the convention from Viinex JS API
        print(json.dumps({'topic': topic, 'data': data}), flush=True)


    @property
    def config(self):
        return self.__config

    def onstart(self):
        Logging.debug("Module is being started")

    def oncommand(self, cmd):
        Logging.debug("Ignoring command", cmd)

    def onstop(self):
        Logging.debug("Module is stopped")

    def run(self):
        self.onstart()
        for line in fileinput.input():
            cmd = json.loads(line)
            self.oncommand(cmd)
        self.onstop()

class Analytics1(ExtProc):
    """
    A class implementing the skeleton of a module for 1-channel video analytics.

    ``onsample`` (and maybe also the ``onformat``) method(s) need to be overridden
    The ``video_source`` property may also be overridden for custom evaluation of a video source name
    (if it's not contained in "init.video_source" JSON property of respective Viinex object).
    """
    def onformat(self,colorspace,width,height):
        pass

    def onsample(self, sample, timestamp):
        pass

    vnxvideo: Vnxvideo
    __lc: LocalClient

    def __init__(self, vv : Vnxvideo = None):
        super().__init__()
        if vv == None:
            self.vnxvideo = Vnxvideo()
        else:
            self.vnxvideo = vv
        
    @property
    def video_source(self):
        return self.config["video_source"] # that's just a vague convention

    def onstart(self):
        super().onstart()
        self.__lc = self.vnxvideo.local_client(self.video_source, self.onformat, self.onsample)
        self.__lc.start()
    
    def onstop(self):
        self.__lc.stop()
        super().onstop()
