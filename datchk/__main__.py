from .arg_handler import ArgHandler
from .dat_handler import DatParser
from .utilities import compare_checksum, get_digest

from os.path import basename,abspath
from pathlib import Path
from rich.console import Console
from rich.table import Table
from tempfile import TemporaryDirectory

console = Console()
args = ArgHandler()
datp = DatParser(args.datfile)

class rom_checker():
    def __init__(self, roms):
        datp.current_rom_found_match = False
        self.valid = False
        self.nidf = False
        self.csna = False
        self.pbin = False
        self.md5 = None
        self.roms = roms
        self.tmpdir = TemporaryDirectory()
        self.results = {'PASS':0,'FAIL':0,
                        'PROC':0,'NIDF':0,
                        'CSNA':0,'PBIN':0}

    def get_node(self, rom) -> None:
        datp.get_rom_node_from_name_exact(basename(rom))

        if datp.current_rom_found_match:
            return
        else:
            self.md5 = get_digest('md5', rom, self.tmpdir)
            datp.get_rom_node_from_md5(self.md5)
            
        if datp.current_rom_found_match:
            self.pbin = True
            self.valid = True
        else:
            self.nidf = True

        return

    def compare(self, rom, checksum)-> None:
        if checksum is not None:
            self.valid = compare_checksum(rom,
                                          checksum,
                                          args.algorithm,
                                          self.tmpdir)
        else:
            self.csna = True


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
            console.print("[{}][ {} ][/{}]  {} [{}]({})[/{}]".format(
            color, stat, color, 
            basename(kwargs["filename"]),
            color, kwargs["entryname"], color), 
            highlight=False)
        else:
            console.print("[{}][ {} ][/{}]  {}".format(
            color, stat, color, basename(kwargs["filename"])), highlight=False)

        self.results[stat] += 1
        self.results['PROC'] += 1

    def check(self) -> None:
        for rom in self.roms:
            datp.current_rom_found_match = False
            self.valid = False
            self.nidf = False
            self.csna = False
            self.pbin = False
            self.md5 = None

            self.get_node(rom)

            if datp.current_rom_found_match:
                self.validate(rom)
            else:
                pass

            # Display results
            if self.nidf:
                self.output_result_line("NIDF", "magenta", filename=basename(rom))
                continue
            
            if self.csna:
                self.output_result_line("CSNA","yellow",filename=basename(rom))
                continue

            if self.pbin:
                if args.failed:
                    pass
                else:
                    self.output_result_line("PBIN","blue", filename=basename(rom), entryname=datp.current_rom.name)
                    continue

            if self.valid:
                if args.failed:
                    pass
                else:
                    self.output_result_line("PASS","green", filename=basename(rom))

            else:
                self.output_result_line("FAIL","red", filename=basename(rom))

            self.tmpdir.cleanup()

def get_romlist_from_path(path: str, is_dir: bool, is_file: bool) -> list:
    if is_dir:
        return [p for p in Path(path).iterdir() if p.is_file()]
    if is_file:
        return [ abspath(path) ]

def check_rom_list(rom_list: list) -> dict:
    rchecker = rom_checker(rom_list)
    rchecker.check()
    return rchecker.results

def main():

    if args.check:
        rom_files_list = get_romlist_from_path(args.path,
                                               args.path_is_d,
                                               args.path_is_f)

        console.print("[+] Started check operation..", style="bold yellow")

        check_results = check_rom_list(rom_files_list)

        console.rule("Results")
        if check_results['PROC'] > 0:
            console.print("{:<15} {}".format("Processed:",      
            check_results['PROC']),style="bold blue")
        if check_results['FAIL'] > 0:
            console.print("{:<15} {}".format("Failed:",         
            check_results['FAIL']),style="bold red")
        if check_results['CSNA'] > 0:
            console.print("{:<15} {}".format("Checksum N/A:",   
            check_results['CSNA']),style="bold yellow")
        if check_results['NIDF'] > 0:
            console.print("{:<15} {}".format("Not in datfile:", 
            check_results['NIDF']),style="bold magenta")

    if args.search:
        with console.status("Searching for matching roms.."):
            results = datp.search_rom_names_w_str(args.search)

        if len(results)-1 > 0:
            console.print("[!] Found {} matching entries..\n".format(len(results)), style="bold yellow")
            
            table = Table(title="Search Results",show_lines=True)
            table.add_column("ID", justify="center", style="bold red", width=4)
            table.add_column("Title")
            table.add_column("MD5", justify="right", style="green")

            for idx,name in results.items():
                table.add_row(str(idx),str(name),str(datp.get_md5_from_name_exact(name)))

            console.print(table)

            while True:
                selection = input("\nSelection (q to QUIT): ")
                if selection.isdigit() and int(selection) <= len(results)-1:
                    datp.get_rom_node_from_name_exact(results[int(selection)])
                    datp.print_current_rom_data()
                    
                    cont = input("\nSelect another ID? [y/n]: ")
                    match cont:
                        case "y" | "Y" | "yes" | "Yes" | "YES":
                            continue
                        case "n" | "N" | "no"  | "No"  | "NO":
                            break
                        case _:
                            break

                elif selection in ["q","Q"]:
                    break
                else:
                    console.print("[-] Invalid selection",style="bold red")
                    continue
        else:
            console.print("[!] No results",style="bold yellow")

if __name__ == '__main__':
    main()
