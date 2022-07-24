import argparse
from os.path import isdir,isfile,abspath

parser = argparse.ArgumentParser(description='Command line datfile parser and validator')
parser.add_argument('path', nargs='?', 
                    type=str, 
                    help='Path to rom file or directory')
parser.add_argument('-d','--datfile', 
                    type=str, 
                    help='Path to .dat file')
parser.add_argument('-r','--rename', 
                    action='store_true', 
                    help='Enable quiet output mode')
parser.add_argument('-c','--check',
                    action='store_true',
                    help='Validate rom files')
parser.add_argument('-a','--algorithm',
                    type=str,
                    help='Set hash algorithm [md5,sha1,sha256]')
parser.add_argument('-f','--failed',
                    action='store_true',
                    help='Display rom entry')
parser.add_argument('-s','--search',
                    type=str,
                    help='Search datfile with a keyword')

args = parser.parse_args()

class ArgHandler():
    def __init__(self):
        self.datfile 	= abspath(args.datfile)
        self.rename 	= args.rename
        self.check      = args.check
        self.algorithm 	= 'md5'
        self.search 	= args.search
        self.failed 	= args.failed
        self.path_is_d 	= False
        self.path_is_f 	= False

        if args.path:
            self.path = abspath(args.path)

        self.validate()
		
    def validate(self):
        # Test for path
        if args.path:
            if isfile(abspath(self.path)):
                self.path_is_f = True
            elif isdir(abspath(self.path)):
                self.path_is_d = True
            else:
                print("[ERROR] Path is not a valid file or directory\nQuitting ..")
                exit()

        # Test for conflicting flags
        if self.check and self.search:
            print("[ERROR] Cannot use --check and --search at the same time\nQuitting ..")
            exit()
			
		# Test for algorithm other than default
        if args.algorithm:
            if args.algorithm in ['md5'   ,'Md5'   ,'MD5',
                                  'sha1'  ,'Sha1'  ,'SHA1',
                                  'sha256','Sha256','SHA256']:
                self.algorithm = args.algorithm.lower()
            else:
                print("[ERROR] Invalid algorithm choice, using default: MD5")
                pass
