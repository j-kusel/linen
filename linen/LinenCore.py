import argparse, os, sys
sys.path.append(os.getcwd())
from inspect import getmembers, isfunction
from linen import commands

def get_functions():
    """get a list of linen commands, strip out private ones"""
    return {f[0]:f[1] for f in getmembers(commands) if isfunction(f[1]) and f[0][0] != '_' and f[1].__module__ == 'linen.commands'}

def main():
    """point of entry for "linen" shell command + arguments"""
    
    # add cwd to system path
    print(sys.path)
    FUNCTIONS = get_functions()
    print(FUNCTIONS)
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help="increase output verbosity", action="store_true")
    parser.add_argument('command', type=str, choices=FUNCTIONS, help="issue a group of Fabric commands using the current configuration file (config.py)")

    args = parser.parse_args()
    if args.verbose:
        print("verbosity turned on")
    FUNCTIONS[args.command]()

if __name__ == '__main__':
    main()
