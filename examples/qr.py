import pyzbar.pyzbar
import datetime
from vnxpy import *

class QrReader(Analytics1):
    def onsample(self, sample : RawSample, timestamp):
        if not sample.is_video:
            return
        ds=pyzbar.pyzbar.decode(sample.gray8())
        # here's what decode() retutns:
        # [Decoded(data=b'datadata', type='QRCODE', rect=Rect(left=236, top=322, width=91, height=102), polygon=[Point(x=236, y=330), Point(x=243, y=424), Point(x=327, y=413), Point(x=321, y=322)])]
        for d in ds:
            if d.type == 'QRCODE':
                left = float(d.rect.left)/float(sample.width)
                top = float(d.rect.top)/float(sample.height)
                right = float(d.rect.width+d.rect.left)/float(sample.width)
                bottom = float(d.rect.height+d.rect.top)/float(sample.height)
                rect = (left, top, right, bottom)
                ts = datetime.datetime.fromtimestamp(timestamp/1000.0, tz=datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
                self.event('QrCode', {'code': d.data.decode("utf-8"), 'rect': rect, 'timestamp': ts})

QrReader().run()
