"""
DATCHK
A command line datfile parser and rom validator written in python.

Written By: Daws
"""

from fileinput import filename
from .arg_handler import ArgHandler
from .dat_handler import DatParser
from .utilities import compare_checksum, get_digest

from collections import Counter
from os.path import basename, abspath
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
)
from tempfile import TemporaryDirectory

console = Console()
args = ArgHandler()
datp = DatParser(args.datfile)


class rom_checker:
    def __init__(self, roms):
        datp.current_rom_found_match = False
        self.valid = False
        self.md5 = None
        self.roms = roms
        self.rom_count = len(self.roms)
        self.tmpdir = TemporaryDirectory()
        self.results = {}

    def get_node(self, rom) -> None:
        datp.get_rom_node_from_name_exact(basename(rom))

        if datp.current_rom_found_match:
            return
        else:
            self.md5 = get_digest("md5", rom, self.tmpdir)
            datp.get_rom_node_from_md5(self.md5)

        if datp.current_rom_found_match:
            match args.algorithm:
                case "sha1":
                    if datp.current_rom.sha1 is None:
                        self.results[basename(rom)] = "CSNA"
                        return
                case "sha256":
                    if datp.current_rom.sha256 is None:
                        self.results[basename(rom)] = "CSNA"
                        return
                case "md5":
                    if datp.current_rom.md5 is None:
                        self.results[basename(rom)] = "CSNA"
                        return

            self.results[basename(rom)] = "PBIN"
            return
        else:
            self.results[basename(rom)] = "NIDF"
            return

    def compare(self, rom, checksum) -> None:
        if checksum is not None:
            if compare_checksum(rom, checksum, args.algorithm, self.tmpdir):
                self.results[basename(rom)] = "PASS"
            else:
                self.results[basename(rom)] = "FAIL"
        else:
            self.results[basename(rom)] = "CSNA"

    def validate(self, rom) -> None:
        match args.algorithm:
            case "sha1":
                self.compare(rom, datp.current_rom.sha1)
            case "sha256":
                self.compare(rom, datp.current_rom.sha256)
            case _:
                if self.md5 is None:
                    self.compare(rom, datp.current_rom.md5)
                else:
                    pass

    def output_result_line(self, stat, color, **kwargs):
        if "entryname" in kwargs:
            console.print(
                "[{}][ {} ][/{}]  {} [{}]({})[/{}]".format(
                    color,
                    stat,
                    color,
                    basename(kwargs["filename"]),
                    color,
                    kwargs["entryname"],
                    color,
                ),
                highlight=False,
            )
        else:
            console.print(
                "[{}][ {} ][/{}]  {}".format(
                    color, stat, color, basename(kwargs["filename"])
                ),
                highlight=False,
            )

    def check(self) -> None:
        progress = Progress(
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        )

        task_id = progress.add_task(
            "[green]Processing...", total=self.rom_count, filename="Blank"
        )

        with progress:
            for rom in self.roms:
                datp.current_rom_found_match = False
                self.valid = False
                self.nidf = False
                self.csna = False
                self.pbin = False
                self.md5 = None

                self.get_node(rom)

                progress.update(task_id, filename=basename(rom))

                if datp.current_rom_found_match:
                    if basename(rom) not in self.results.keys():
                        self.validate(rom)
                    else:
                        pass
                else:
                    pass

                progress.update(task_id, advance=1)

                self.tmpdir.cleanup()

            progress.update(task_id, filename="Complete!")

    def show_check_results(self):
        if args.failed and "FAIL" not in self.results:
            console.print("\n[+] All roms have passed verification", style="bold blue")
        else:
            console.rule("Results")
            for rom, ocode in self.results.items():
                match ocode:
                    case "PASS":
                        if args.failed:
                            pass
                        else:
                            self.output_result_line(ocode, "green", filename=rom)
                    case "NIDF":
                        self.output_result_line(ocode, "magenta", filename=rom)
                    case "CSNA":
                        self.output_result_line(ocode, "yellow", filename=rom)
                    case "PBIN":
                        if args.failed:
                            pass
                        else:
                            # self.output_result_line(
                            #     "PBIN",
                            #     "blue",
                            #     filename=rom,
                            #     entryname=datp.current_rom.name,
                            # )
                            self.output_result_line(ocode, "blue", filename=rom)
                    case _:
                        self.output_result_line("FAIL", "red", filename=basename(rom))

    def show_statistics(self):
        console.rule("Statistics")
        stats = Counter(self.results.values())
        if self.rom_count > 0:
            console.print(
                "{:<15} {}".format("Processed:", self.rom_count),
                style="bold blue",
            )

        if stats["PASS"] > 0:
            console.print(
                "{:<15} {}".format("Passed:", stats["PASS"]), style="bold green"
            )
        if stats["FAIL"] > 0:
            console.print(
                "{:<15} {}".format("Failed:", stats["FAIL"]), style="bold red"
            )
        if stats["CSNA"] > 0:
            console.print(
                "{:<15} {}".format("Checksum N/A:", stats["CSNA"]),
                style="bold yellow",
            )
        if stats["NIDF"] > 0:
            console.print(
                "{:<15} {}".format("Not in datfile:", stats["NIDF"]),
                style="bold magenta",
            )


def get_romlist_from_path(path: str, is_dir: bool, is_file: bool) -> list:
    if is_dir:
        return [p for p in Path(path).iterdir() if p.is_file()]
    if is_file:
        return [abspath(path)]


def check_rom_list(rom_list: list) -> dict:
    rchecker = rom_checker(rom_list)
    rchecker.check()
    rchecker.show_check_results()
    rchecker.show_statistics()


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
