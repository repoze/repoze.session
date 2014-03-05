import sys

PY3 = sys.version_info[0] >= 3
PY2 = not PY3

if PY3: #pragma NO COVER Py3k

    import pickle

    def get_code(method):
        return method.__code__

else: #pragma NO COVER Python 2

    import cPickle as pickle

    def get_code(method):
        return method.im_func.func_code
