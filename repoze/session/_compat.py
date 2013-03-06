import sys

PY3 = sys.version_info[0] >= 3
PY2 = not PY3

if PY3:

    import pickle

    def get_code(method):
        return method.__code__
else:

    import cPickle as pickle

    def get_code(method):
        return method.im_func.func_code
