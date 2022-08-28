"""
DATCHK
A command line datfile parser and rom validator written in python.

Written By: Daws
"""

from .arg_handler import ArgHandler
from .check import Check
from .dat_handler import DatParser
from .search import Search
from rich.console import Console

args = ArgHandler()
console = Console()
dat = DatParser(args.datfile)


def main():

    if args.check:
        chk = Check(console, dat, args)
        chk.check()

    if args.search:
        dat_search = Search(console, dat)
        dat_search.search(args.search)


if __name__ == "__main__":
    main()
