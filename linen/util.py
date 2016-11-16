from linen.error import PassError
import sys

def checkpass():
    """confirm the validity of the passwords.py file in the current working directory"""
    try:
        from passwords import PASSWORDS
        try:
            if type(PASSWORDS) is not dict:
                if len(str(PASSWORDS)) < 8:
                    raise PassError('passwords must be at least 8 characters')
                PASSWORDS = {}
                for k in ['SUPER', 'Django', 'MySQL']:
                    PASSWORDS[k] = str(PASSWORDS)
            for p in PASSWORDS:
                if not PASSWORDS[p]:
                    PASSWORDS[p] = PASSWORDS['SUPER']
            return PASSWORDS
        except PassError as p:
            raise p(p.message)
    except ImportError:
        sys.stderr.write('set a PASSWORDS dictionary in a passwords.py file\n')
        sys.exit(1)

def globfiles(dir, ignore, ext):
    """search a directory for files with certain extensions, ignoring list of specified files.
    returns a {<filename>: <path>} dictionary."""
    tempfiles = glob.glob('{}/*.{}'.format(dir, ext))
    badfiles = list(set(ignore.append('__init__.py'))) # filter duplicates!
    return {os.path.basename(tf):tf for tf in tempfiles if os.path.exists(tf) and os.path.basename(tf) not in badfiles}
