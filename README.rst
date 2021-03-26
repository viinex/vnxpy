vnxpy is a module for integration of a vnxvideo library with Python.

vnxvideo is a set of lower-level video-related components which are a part of Viinex software (https://viinex.com)
The source code of vnxvideo is available at https://github.com/viinex/vnxvideo

vnxpy wraps some of APIs exposed by vnxvideo, namely the local transport (client) and raw video sample. 
This allows for Python code to access raw video published by Viinex, in order to perform video analytics on it.

Another thing vnxpy provides is the implementation of a skeleton of an "external process" which can be used by Viinex as an analytics module.

Some examples available in the "examples" subfolder: these are analytics modules for QR code recognition (qr.py) 
and for detection of motion direction and quantity (hsmd). NOTE: you'll need scikit-image, opencv, pyzbar packages 
installed in order to run examples.