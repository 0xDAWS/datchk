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
    "path", nargs="?", type=str, help="Path to rom file or directory", metavar="PATH"
)
parser.add_argument("-d", "--datfile", help="Path to datfile", metavar="PATH")
parser.add_argument(
    "-r",
    "--rename",
    action="store_true",
    help="Rename an incorrectly named file with its datfile entry name",
)
parser.add_argument("-c", "--check", action="store_true", help="Validate rom files")
parser.add_argument(
    "-a",
    "--algorithm",
    help="Set hash algorithm [md5,sha1,sha256]",
    metavar="ALGORITHM",
)
parser.add_argument(
    "-f",
    "--failed",
    action="store_true",
    help="Output only results with fail output codes",
)
parser.add_argument(
    "-s", "--search", help="Search datfile with a keyword", metavar="KEYWORD"
)

args = parser.parse_args()


class ArgHandler:
    def __init__(self):
        if args.datfile is not None:
            self.datfile = abspath(args.datfile)
        else:
            print("[ERROR] No datfile was provided, use -d or --datfile")
            exit()
        self.rename = args.rename
        self.check = args.check
        self.algorithm = "md5"
        self.search = args.search
        self.failed = args.failed
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
