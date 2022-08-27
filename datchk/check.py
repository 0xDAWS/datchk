from .utilities import HashHandler, extract_archive

from collections import Counter
from os.path import basename, getsize
from pathlib import Path
from rich.console import group, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
)
from tempfile import TemporaryDirectory

# from rich.logging import RichHandler
# import logging

# import time


# FORMAT = "%(message)s"
# logging.basicConfig(
#     level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
# )
# log = logging.getLogger("rich")


class Check:
    def __init__(self, roms, datfile, console, args):
        self.args = args
        self.console = console
        self.dat = datfile
        self.dat.current_rom_found_match = False
        self.valid = False
        self.md5: str = ""
        self.roms = roms
        self.rom_count = len(self.roms)
        self.rom_digests = {}
        self.tmpdir = TemporaryDirectory()
        self.hasher = HashHandler()

        # ocode lookup dicts
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
        self.current_rom_filename = "None"
        self.current_rom_filesize: int = 0

        # Results
        self.results: dict = {}
        self.results_passed: int = 0
        self.results_count: dict = None
        self.pbin_map: dict = {}

        # Progress Bar
        self.progress: Progress = Progress(
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        )
        self.task_total = self.progress.add_task(
            "[green]Total...", total=self.rom_count, filename=""
        )

    def update_rom_digests(self) -> None:
        self.rom_digests = {
            "md5": self.dat.current_rom.md5,
            "sha1": self.dat.current_rom.sha1,
            "sha256": self.dat.current_rom.sha256,
        }

    def get_node(self, rom) -> None:
        self.dat.get_rom_node_from_name_exact(self.current_rom_filename)

        if self.dat.current_rom_found_match:
            self.update_rom_digests()
            return
        else:
            self.dat.get_rom_node_from_md5(self.md5)

        if self.dat.current_rom_found_match:
            self.update_rom_digests()

            if not self.rom_digests[self.args.algorithm]:
                return
            else:
                self.results[self.current_rom_filename] = "PBIN"
                self.pbin_map[self.current_rom_filename] = self.dat.current_rom.name
                return
        else:
            self.results[self.current_rom_filename] = "NIDF"
            return

    def compare(self, rom, checksum) -> None:

        if checksum is not None:
            if self.hasher.compare_checksum(rom, checksum, self.args.algorithm):
                self.results_passed += 1
            else:
                self.results[self.current_rom_filename] = "FAIL"
        else:
            self.results[self.current_rom_filename] = "CSNA"

    def validate(self, rom) -> None:
        self.compare(rom, self.rom_digests[self.args.algorithm])

    def build_status_table(self):
        self.results_count = Counter(self.results.values())
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
        # table.add_row(
        #     "[bold default]{}[/bold default]: [green]{}[/green]".format(
        #         "Status", self.status
        #     ),
        # )
        table.add_row(self.progress)

        return Panel(
            table,
            title="[bold default]" + ("Progress"),
            border_style="green",
            padding=(2, 2),
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

    def check(self) -> None:
        check_panel = self.build_check_panel()

        with Live(
            check_panel,
            refresh_per_second=20,
            screen=True,
        ) as live_check:
            # with self.progress:
            self.status = "Processing"

            for rom in self.roms:
                self.dat.current_rom_found_match = False
                self.current_rom_filename = basename(rom)

                # If a zip or 7z archive is detected from file extension
                # we set rom to the tmp file path
                if Path(rom).suffix in [".zip", ".7z"]:
                    rom_name = extract_archive(rom, self.tmpdir)
                    rom = Path(self.tmpdir.name, rom_name)

                self.md5 = self.hasher.get_digest(rom, "md5")

                # log.info(
                #     f"Current: {rom}\nName:{self.current_rom_filename}\nMD5:{self.md5}"
                # )

                check_panel = self.build_check_panel()
                self.progress.update(
                    self.task_total, filename=self.current_rom_filename
                )
                live_check.update(check_panel)

                self.get_node(rom)

                if self.dat.current_rom_found_match:
                    if self.current_rom_filename not in self.results.keys():
                        self.validate(rom)
                    else:
                        pass
                else:
                    pass

                self.progress.update(self.task_total, advance=1)

                self.tmpdir.cleanup()

            self.progress.update(self.task_total, filename="Complete!")

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
                    fail_tree.add(f"[{self.ocode_color_lkup[ocode]}]{rom_name}")
                case "CSNA":
                    csna_tree.add(f"[{self.ocode_color_lkup[ocode]}]{rom_name}")
                case "NIDF":
                    nidf_tree.add(f"[{self.ocode_color_lkup[ocode]}]{rom_name}")
                case "PBIN":
                    branch = pbin_tree.add(
                        f"[{self.ocode_color_lkup[ocode]}]{rom_name}"
                    )
                    branch.add(f"Name in Datfile: [green]{self.pbin_map[rom_name]}")

        if no_warnings:
            self.console.print(
                "[bold green] All files passed, no failures or warnings to report.."
            )
        else:
            self.console.rule("Warnings and Failures")
            self.console.print(report_tree)
