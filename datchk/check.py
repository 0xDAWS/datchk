from .utilities import HashHandler, extract_archive

from collections import Counter
from os.path import abspath, basename
from pathlib import Path
from rich.console import group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table, Column
from rich.align import Align
from rich.progress import (
    Progress,
    # TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
    SpinnerColumn,
)
from tempfile import TemporaryDirectory

import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")


class Check:
    def __init__(self, console, datfile, args):
        self.args = args
        self.console = console
        self.dat = datfile
        self.dat.current_rom_found_match = False
        self.roms = self.get_romlist_from_path(
            self.args.path, self.args.path_is_d, self.args.path_is_f
        )
        self.rom_count = len(self.roms)
        self.rom_digests = {}
        self.tmpdir = TemporaryDirectory()
        self.hasher = HashHandler()

        # lookup dicts
        self.ocode_color_lkup = {
            "PASS": "green",
            "FAIL": "red",
            "CSNA": "yellow",
            "PBIN": "blue",
            "NIDF": "magenta",
        }

        self.status_color_lkup = {
            "Waiting": "yellow",
            "Processing": "blue",
            "Completed": "green",
        }

        # Current State
        # self.current_status = "Waiting"
        self.md5: str = None
        self.current_rom_filename: str = ""
        self.current_rom_filesize: int = 0
        self.is_archive: bool
        self.archive_filename: str

        # Results
        self.results: dict = {}
        self.results_passed: int = 0
        self.results_count: dict = None
        self.pbin_map: dict = {}
        self.arc_map: dict = {}

        # Progress Bar
        self.progress: Progress = Progress(
            SpinnerColumn(table_column=Column(ratio=1)),
            MofNCompleteColumn(table_column=Column(ratio=1)),
            BarColumn(bar_width=None, table_column=Column(ratio=2)),
            TaskProgressColumn(table_column=Column(ratio=1)),
            TimeElapsedColumn(table_column=Column(ratio=1)),
            # TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            refresh_per_second=20,
            # expand=True,
        )
        self.task_total = self.progress.add_task(
            "[green]Total...", total=self.rom_count, filename=""
        )

    def get_romlist_from_path(self, path: str, is_dir: bool, is_file: bool) -> list:
        if is_dir:
            return [p for p in Path(path).iterdir() if p.is_file()]
        if is_file:
            return [abspath(path)]

    def update_rom_digests(self) -> None:
        self.rom_digests = {
            "md5": self.dat.current_rom.md5,
            "sha1": self.dat.current_rom.sha1,
            "sha256": self.dat.current_rom.sha256,
        }

    def get_node(self, rom) -> None:
        """
        TODO:
        Currently if a match can't be found from the filename
        The file MD5 is calculated and then that digest is used to search the
        datfile. This is fine if the user is using the default MD5
        for the entire check, but is adding extra computations
        if SHA1 or SHA256 is being used as it will calculate
        the digest for both the MD5 and the users chosen algorithm

        A solution will need to be implemented which can either uses
        another piece of data from the dat file, filesize+CRC or the
        digest of the chosen algorithm (if available)
        """
        self.dat.get_rom_node_from_name_exact(self.current_rom_filename)

        if self.dat.current_rom_found_match:
            if self.args.debug and not self.args.live:
                log.info(f"\nFOUND_MATCH_W_NAME:{self.current_rom_filename}")
            self.update_rom_digests()
            return
        else:
            self.md5 = self.hasher.get_digest(rom, "md5")
            self.dat.get_rom_node_from_md5(self.md5)

        if self.dat.current_rom_found_match:
            if self.args.debug and not self.args.live:
                log.info(f"\nFOUND_MATCH_W_DGST:{self.current_rom_filename}")
            self.update_rom_digests()

            if not self.rom_digests[self.args.algorithm]:
                return
            else:
                """
                If we find a match based on the MD5 digest and not the name of the file itself,
                the file is a valid but the filename is not, so we add to self.results with the
                PBIN ocode (Passed But Incorrect Name) as the value.
                For PBIN results we also want to suggest the correct name to the user so the
                filename is added to self.pbin_map dict with the value of the entry-name contained
                in the datfile.
                """
                if self.args.debug and not self.args.live:
                    log.warn(f"RESULT_PBIN:{rom}")

                if self.is_archive:
                    self.results[self.archive_filename] = "PBIN"
                    self.pbin_map[self.archive_filename] = self.dat.current_rom.name
                else:
                    self.results[self.current_rom_filename] = "PBIN"
                    self.pbin_map[self.current_rom_filename] = self.dat.current_rom.name
                return
        else:
            if self.args.debug and not self.args.live:
                log.info(f"RESULT_NIDF:{rom}")

            if self.is_archive:
                self.results[self.archive_filename] = "NIDF"
            else:
                self.results[self.current_rom_filename] = "NIDF"
            return

    def compare(self, rom, checksum) -> None:
        # TODO: This needs some refactoring
        if checksum is not None:
            if self.md5 and self.args.algorithm == "md5":
                if self.md5 == checksum:
                    if self.args.debug and not self.args.live:
                        log.info(f"RESULT_PASS:{rom}")
                    self.results_passed += 1
                else:
                    if self.args.debug and not self.args.live:
                        log.info(f"RESULT_FAIL:{rom}")
                    if self.is_archive:
                        self.results[self.archive_filename] = "FAIL"
                    else:
                        self.results[self.current_rom_filename] = "FAIL"
                return
            else:
                if self.hasher.compare_checksum(rom, checksum, self.args.algorithm):
                    if self.args.debug and not self.args.live:
                        log.info(f"RESULT_PASS:{rom}")
                    self.results_passed += 1
                else:
                    if self.args.debug and not self.args.live:
                        log.info(f"RESULT_FAIL:{rom}")
                    if self.is_archive:
                        self.results[self.archive_filename] = "FAIL"
                    else:
                        self.results[self.current_rom_filename] = "FAIL"
                return
        else:
            if self.args.debug and not self.args.live:
                log.info(f"RESULT_CSNA:{rom}")
            if self.is_archive:
                self.results[self.archive_filename] = "CSNA"
            else:
                self.results[self.current_rom_filename] = "CSNA"
            return

    def validate(self, rom) -> None:
        self.compare(rom, self.rom_digests[self.args.algorithm])

    def build_status_table(self):
        try:
            self.results_count = Counter(self.results.values())
        except TypeError as e:
            log.error(e)
            self.console.print(f"Dumping results..\n{self.results}")
            exit()
        table = Table(show_header=False)
        table.add_column("Result")
        table.add_column("Count", width=5, min_width=5, justify="right")
        table.add_row(
            "Passed",
            "[green]{}[/green]".format(str(self.results_passed)),
        )
        table.add_row(
            "Failed",
            "[green]{}[/green]".format(str(self.results_count["FAIL"])),
        )
        table.add_row(
            "Passed But Incorrect Name",
            "[green]{}[/green]".format(str(self.results_count["PBIN"])),
        )
        table.add_row(
            "CheckSum Not Available",
            "[green]{}[/green]".format(str(self.results_count["CSNA"])),
        )
        table.add_row(
            "Not In DatFile",
            "[green]{}[/green]".format(str(self.results_count["NIDF"])),
        )

        return Align.center(table)

    def build_progress_panel(self):
        table = Table.grid()
        table.add_row(f"Current File: [bold blue]{self.current_rom_filename}")
        table.add_row(self.progress)

        return Panel(
            table,
            title="[bold default]" + ("Progress"),
            border_style="green",
            padding=(2, 2),
            expand=True,
        )

    def build_check_panel(self) -> None:
        return Panel(
            self.get_panels(),
            title="[bold default]" + ("Checking"),
            border_style="bold blue",
            padding=(2, 2),
        )

    @group()
    def get_panels(self):
        yield self.build_status_table()
        yield self.build_progress_panel()

    def determine_file_or_archive(self, f):
        return Path(f).suffix in [".zip", ".7z"]

    def check(self) -> None:
        self.console.print("[+] Started check operation..", style="bold yellow")
        self.console.print(f"[*] Found {len(self.roms)} files..", style="bold yellow")

        check_panel = self.build_check_panel()

        if self.args.live:
            display_mgr = Live(
                check_panel,
                refresh_per_second=20,
                screen=True,
            )
        else:
            display_mgr = self.progress

        with display_mgr:
            self.status = "Processing"

            for rom in self.roms:
                # Reset the state
                self.md5 = None
                self.dat.current_rom_found_match = False
                self.is_archive = self.determine_file_or_archive(rom)

                # If a zip or 7z archive is detected from file extension
                # we set rom to the tmp file path
                if self.is_archive:
                    self.archive_filename = basename(rom)
                    self.current_rom_filename = extract_archive(rom, self.tmpdir)
                    rom = Path(self.tmpdir.name, self.current_rom_filename)
                    self.arc_map[self.archive_filename] = self.current_rom_filename
                    if self.args.debug:
                        log.warn(
                            f"\nARCHIVE_DETECTED: Archive Name:{self.archive_filename}\nCompressed Filename:{self.current_rom_filename}"
                        )
                else:
                    self.current_rom_filename = basename(rom)

                check_panel = self.build_check_panel()
                self.progress.update(
                    self.task_total, filename=self.current_rom_filename
                )
                if self.args.live:
                    display_mgr.update(check_panel)

                self.get_node(rom)

                if self.dat.current_rom_found_match:
                    if self.is_archive:
                        if self.archive_filename not in self.results.keys():
                            self.validate(rom)
                        else:
                            pass
                    else:
                        if self.current_rom_filename not in self.results.keys():
                            self.validate(rom)
                        else:
                            pass
                else:
                    pass

                self.progress.update(self.task_total, advance=1)

                self.tmpdir.cleanup()

            self.progress.update(self.task_total, filename="Complete!")

        self.show_statistics()
        self.generate_report_tree()

    def show_statistics(self):
        self.console.rule("Statistics")
        self.results_count = Counter(self.results.values())
        results_table = Table(show_header=False, show_lines=True)
        results_table.add_column("Result")
        results_table.add_column("Count")

        results_table.add_row("Processed", f"[bold green]{self.rom_count}")
        results_table.add_row("Passed", f"[bold green]{self.results_passed}")
        results_table.add_row(
            "Passed But Incorrect Name", f"[bold green]{self.results_count['PBIN']}"
        )
        results_table.add_row("Failed", f"[bold green]{self.results_count['FAIL']}")
        results_table.add_row(
            "CheckSum N/A", f"[bold green]{self.results_count['CSNA']}"
        )
        results_table.add_row(
            "Not In DatFile", f"[bold green]{self.results_count['NIDF']}"
        )

        self.console.print(Align.center(results_table))

    def generate_report_tree(self):
        from rich.tree import Tree

        report_tree = Tree("Warnings and Failures", hide_root=True)
        no_warnings = False

        if self.results_count["FAIL"] > 0:
            fail_tree = report_tree.add("Failed")
        if self.results_count["CSNA"] > 0:
            csna_tree = report_tree.add("Checksum N/A")
        if self.results_count["NIDF"] > 0:
            nidf_tree = report_tree.add("Not In DatFile")
        if self.results_count["PBIN"] > 0:
            pbin_tree = report_tree.add("Passed But Incorrect Name")
        if not self.results_count:
            no_warnings = True

        for rom_name, ocode in self.results.items():
            match ocode:
                case "FAIL":
                    if self.determine_file_or_archive(rom_name):
                        fail_tree.add(
                            f"[bold default](A) [/bold default][{self.ocode_color_lkup[ocode]}]{rom_name}[bold default] -> [/bold default][green]{self.arc_map[rom_name]}"
                        )
                    else:
                        fail_tree.add(f"[{self.ocode_color_lkup[ocode]}]{rom_name}")
                case "CSNA":
                    if self.determine_file_or_archive(rom_name):
                        csna_tree.add(
                            f"[bold default](A) [/bold default][{self.ocode_color_lkup[ocode]}]{rom_name}[bold default] -> [bold default][green]{self.arc_map[rom_name]}"
                        )
                    else:
                        csna_tree.add(f"[{self.ocode_color_lkup[ocode]}]{rom_name}")
                case "NIDF":
                    if self.determine_file_or_archive(rom_name):
                        nidf_tree.add(
                            f"[bold default](A) [/bold default][{self.ocode_color_lkup[ocode]}]{rom_name}[bold default] -> [bold default][green]{self.arc_map[rom_name]}"
                        )
                    else:
                        nidf_tree.add(f"[{self.ocode_color_lkup[ocode]}]{rom_name}")
                case "PBIN":
                    if self.determine_file_or_archive(rom_name):
                        branch = pbin_tree.add(
                            f"[bold default](A) [/bold default][{self.ocode_color_lkup[ocode]}]{rom_name}[bold default] -> [bold default][green]{self.arc_map[rom_name]}"
                        )
                    else:
                        branch = pbin_tree.add(
                            f"[{self.ocode_color_lkup[ocode]}]{rom_name}"
                        )
                    branch.add(f"Suggested Name: [green]{self.pbin_map[rom_name]}")

        if no_warnings:
            self.console.print(
                "[bold green] All files passed, no failures or warnings to report.."
            )
        else:
            self.console.rule("Warnings and Failures")
            self.console.print(report_tree)
