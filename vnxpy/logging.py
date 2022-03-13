import sys

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
