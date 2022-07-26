"""
DATCHK
A command line datfile parser and rom validator written in python.

Written By: Daws
"""

import argparse
from os.path import isdir, isfile, abspath


class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=80)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ", ".join(action.option_strings) + " " + args_string


fmt = lambda prog: CustomHelpFormatter(prog)
parser = argparse.ArgumentParser(
    formatter_class=fmt, description="Command line datfile parser and validator"
)
parser.add_argument(
    "path", nargs="?", type=str, help="Path to file or directory", metavar="PATH"
)
parser.add_argument("-f", "--file", help="Path to datfile", metavar="PATH")
parser.add_argument(
    "-r",
    "--rename",
    action="store_true",
    help="Rename an incorrectly named file with its datfile entry name",
)
parser.add_argument(
    "-c", "--check", action="store_true", help="Validate file or directory of files"
)
parser.add_argument(
    "-a",
    "--algorithm",
    help="Set hash algorithm [md5,sha1,sha256]",
    metavar="ALGORITHM",
)
parser.add_argument(
    "-s", "--search", help="Search datfile with a keyword", metavar="KEYWORD"
)
parser.add_argument(
    "-l",
    "--live",
    action="store_true",
    help="Check operation will use live display",
)
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    help="Enable debug logging",
)

args = parser.parse_args()


class ArgHandler:
    def __init__(self):
        if args.file is not None:
            self.datfile = abspath(args.file)
        else:
            print("[ERROR] No datfile was provided, use -d or --datfile")
            exit()
        self.rename = args.rename
        self.check = args.check
        self.debug = args.debug
        self.algorithm = "md5"
        self.search = args.search
        self.live = args.live
        self.path_is_d = False
        self.path_is_f = False

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
            print(
                "[ERROR] Cannot use --check and --search at the same time\nQuitting .."
            )
            exit()

        # Test for algorithm other than default
        if args.algorithm:
            if args.algorithm in [
                "md5",
                "Md5",
                "MD5",
                "sha1",
                "Sha1",
                "SHA1",
                "sha256",
                "Sha256",
                "SHA256",
            ]:
                self.algorithm = args.algorithm.lower()
            else:
                print("[ERROR] Invalid algorithm choice, using default: MD5")
                pass
