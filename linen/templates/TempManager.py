import os
from linen.util import globfiles
from fabric.api import run

def _glob():
    """globfiles wrapper to return linen template files"""
    dirpath = os.path.dirname(os.path.abspath(__file__))
    ext = '.py'
    ignore = [__file__,]
    return globfiles(dirpath, ignore, ext)

def mv(dir, force=False, verbose=True):
    """Fabric 'run' wrapper for moving blank linen template files to <dir> directory (Django root)"""
    templates = _glob()
    workingdir = globfiles(dir, [], '.py')
    flag = '-f' if force else '-i'
    flag = verbose and flag.append('v') or flag
    for t in templates:
        run('mv {0} {1}/{3} {2}/{3}'.format(templates[t], dir, t))
        
