vnxpy is a module for integration of a vnxvideo library with Python.

vnxvideo is a set of lower-level video-related components which are a part of Viinex software (https://viinex.com)
The source code of vnxvideo is available at https://github.com/viinex/vnxvideo

vnxpy wraps some of APIs exposed by vnxvideo, namely the local transport (client) and raw video sample. 
This allows for Python code to access raw video published by Viinex, in order to perform video analytics on it.

Another thing vnxpy provides is the implementation of a skeleton of an "external process" which can be used by Viinex as an analytics module.

Some examples available in the "examples" subfolder: these are analytics modules for QR code recognition (qr.py) 
and for detection of motion direction and quantity (hsmd). NOTE: you'll need scikit-image, opencv, pyzbar packages 
installed in order to run examples.

Installation and usage
======================
The `vnxpy` package itself is quite simple and only depends on `numpy`. 
So in order to use it, one needs to install this package using `pip`, and maybe also install the `numpy` pachage.
This is sufficient to use `vnxpy` in your Python code.
If you'd like to run examples provided, you'll also need the `scikit-image` for the `hsmd` example, and `pyzbar` 
for the QR code reader example. These both are also installable with `pip`. Detailed instructions are given below.


Windows
-------
On Windows, most hygienic way would be to use an "embedded" Python package which is downloadable from 
https://www.python.org/downloads/windows/ (for example this one https://www.python.org/ftp/python/3.8.9/python-3.8.9-embed-amd64.zip).
This won't interfere with existing Python install; neither it would ask unnecessary questions on PATH modification, and so on.
Unpack this archive somewhere (let's assume that would be the `c:\python-3.8.9-embed-amd64` folder). After that, modify the `python38._pth` file
in that folder so that the file reads
```
python38.zip
.
lib\site-packages

# Uncomment to run site.main() automatically
#import site
```
(e.g. the line `lib\site-packages` needs to be added).
Also, download the `get-pip.py` script from https://bootstrap.pypa.io/get-pip.py.
Run that script using the embedded Python:
```
c:\python-3.8.9-embed-amd64\python.exe \path\to\get-pip.py
```
After this script runs successfully, you should be able to use `pip` in order to install required packages:
```
c:\python-3.8.9-embed-amd64\python.exe -m pip install numpy scikit-image pyzbar
c:\python-3.8.9-embed-amd64\python.exe -m pip install \path\to\vnxpy
```
Upon completion of these steps, the examples from vnxpy should be runnable with commads like:
```
c:\python-3.8.9-embed-amd64\python.exe \path\to\vnxpy\examples\qr.py
c:\python-3.8.9-embed-amd64\python.exe \path\to\vnxpy\examples\hsmd
```

Linux
-----
On Linux, use your local Python 3 installation. Add the vnxpy module by checking out this repository and issuing the commands
```
pip install numpy scikit-image pyzbar /path/to/vnxpy
```
Upon completion of these steps, the examples from vnxpy should be runnable with commands like:
```
python /path/to/vnxpy/examples/qr.py
python /path/to/vnxpy/examples/hsmd
```

Viinex configuration
====================
In order to run custom video analytics using the `vnxpy` module, including the examples included with this repository, 
Viinex needs a specific configuration. Respective configuration examples are given in files `examples/hsmd-config.json` 
and `examples/qr.json`. Both of these files are partial configuration; they assume that there is another part which contains the
video source named `cam1`, as well as the web server `web0` and WebRTC server `webrtc0`.

What both of example configurations do is they create a video renderer which decodes video stream from `cam1` video source 
and publishes this stream using Viinex local transport mechanism. Also, an "external process" mechanism is used in order to
run Python with the source code of vnxpy examples. Depending on the path to Python and to `vnxpy` directory containing 
the source code of examples, one would need to edit the paths ("executable" and "args" properties of the "process" object 
in Viinex config).