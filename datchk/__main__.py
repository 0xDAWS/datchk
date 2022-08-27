"""
DATCHK
A command line datfile parser and rom validator written in python.

Written By: Daws
"""

from fileinput import filename
from turtle import update
from .arg_handler import ArgHandler
from .check import Check
from .dat_handler import DatParser

from os.path import abspath
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()
args = ArgHandler()
datp = DatParser(args.datfile)


def get_romlist_from_path(path: str, is_dir: bool, is_file: bool) -> list:
    if is_dir:
        return [p for p in Path(path).iterdir() if p.is_file()]
    if is_file:
        return [abspath(path)]


def check_rom_list(rom_list: list) -> dict:
    chk = Check(rom_list, datp, console, args)
    chk.check()
    chk.show_statistics()
    chk.generate_report_tree()


def main():

    if args.check:
        rom_files_list = get_romlist_from_path(
            args.path, args.path_is_d, args.path_is_f
        )

        console.print("[+] Started check operation..", style="bold yellow")
        console.print(
            "[*] Found {} roms..".format(len(rom_files_list)), style="bold yellow"
        )

        check_rom_list(rom_files_list)

    if args.search:
        with console.status("Searching for matching roms.."):
            results = datp.search_rom_names_w_str(args.search)

        if results:
            console.print(
                "[!] Found {} matching entries..\n".format(len(results)),
                style="bold yellow",
            )

            table = Table(title="Search Results", show_lines=True)
            table.add_column("ID", justify="center", style="bold red", width=4)
            table.add_column("Title")
            table.add_column("MD5", justify="right", style="green")

            for idx, name in results.items():
                table.add_row(
                    str(idx), str(name), str(datp.get_md5_from_name_exact(name))
                )

            console.print(table)

            while True:
                selection = input("\nSelection (q to QUIT): ")
                if selection.isdigit() and int(selection) <= len(results) - 1:
                    datp.get_rom_node_from_name_exact(results[int(selection)])
                    datp.print_current_rom_data()

                    cont = input("\nSelect another ID? [y/n]: ")
                    match cont:
                        case "y" | "Y" | "yes" | "Yes" | "YES":
                            continue
                        case "n" | "N" | "no" | "No" | "NO":
                            break
                        case _:
                            break

                elif selection in ["q", "Q"]:
                    break
                else:
                    console.print("[-] Invalid selection", style="bold red")
                    continue
        else:
            console.print("[!] No results", style="bold yellow")


if __name__ == "__main__":
    main()
