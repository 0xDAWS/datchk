from .arg_handler import ArgHandler
from .dat_handler import DatParser
from .dat_hasher import compare_rom_checksum, get_digest

from os.path import basename,abspath
from pathlib import Path
from rich.console import Console
from rich.table import Table
from tempfile import TemporaryDirectory

console = Console()
args = ArgHandler()
datp = DatParser(args.datfile)

def gen_romfile_list_from_path(path: str, is_dir: bool, is_file: bool) -> list:
    if is_dir:
        return [p for p in Path(path).iterdir() if p.is_file()]
    if is_file:
        return [ abspath(path) ]
	
def check_roms(rom_list: list, arg_verbose: bool, arg_failed: bool) -> dict:
    results = {'PASS':0,'FAIL':0,'PROC':0,'NIDF':0,'CSNA':0}
    tmpdir = TemporaryDirectory()

    for rom in rom_list:

        # Reset the check states
        datp.current_rom_found_match = False
        valid_rom = False
        rom_md5 = None

        # Attempt to find rom node using the rom filename
        datp.get_rom_node_from_name_exact(basename(rom))

        # If match not found attempt to find the rom using its md5 digest
        if not datp.current_rom_found_match:
            rom_md5 = get_digest('md5', rom, tmpdir)
            datp.get_rom_node_from_md5(rom_md5)

        # If still no match add to NIDF results
        if not datp.current_rom_found_match:
            console.print("[magenta]{:<15}[/magenta] {}".format("[ NIDF ]", basename(rom)),highlight=False)
            results['NIDF'] += 1
            results['PROC'] += 1
            continue

        # Checksum validation
        match args.algorithm:
            case "md5":
                if rom_md5 is None:
                    valid_rom = compare_rom_checksum(args.algorithm,rom,datp.current_rom.md5,tmpdir)
                else:
                    if rom_md5 == datp.current_rom.md5:
                        valid_rom = True
                    else:
                        pass
            case "sha1":
                valid_rom = compare_rom_checksum(args.algorithm,rom,datp.current_rom.sha1,tmpdir)
            case "sha256":
                if datp.current_rom.sha256 is not None:
                    valid_rom = compare_rom_checksum(args.algorithm,rom,datp.current_rom.sha256,tmpdir)
                else:
                    console.print("[yellow]{:<15}[/yellow] {}".format("[ CSNA ]", basename(rom)),highlight=False)
                    results['CSNA'] += 1
                    results['PROC'] += 1
                    continue

        # Output results
        if valid_rom:
            if arg_failed:
                pass
            else:
                console.print("[green]{:<15}[/green] {}".format("[ PASS ]", basename(rom)),highlight=False)
                results['PASS'] += 1
        else:
            console.print("[red]{:<15}[/red] {}".format("[ FAIL ]",basename(rom)),highlight=False)
            results['FAIL'] += 1

        results['PROC'] += 1

        tmpdir.cleanup()

    return results

def main():
    console.rule("Datchk")

    if args.check:
        rom_files_list = gen_romfile_list_from_path(args.path, 
                                                    args.path_is_d, 
                                                    args.path_is_f)

        console.print("[+] Started check operation..", style="bold yellow")

        check_results = check_roms(rom_files_list, args.verbose, args.failed)

        console.rule("Results")
        if check_results['PROC'] > 0:
            console.print("{:<15} {}".format("Processed:",      check_results['PROC']),style="bold blue")
        if check_results['FAIL'] > 0:
            console.print("{:<15} {}".format("Failed:",         check_results['FAIL']),style="bold red")
        if check_results['CSNA'] > 0:
            console.print("{:<15} {}".format("Checksum N/A:",   check_results['CSNA']),style="bold yellow")
        if check_results['NIDF'] > 0:
            console.print("{:<15} {}".format("Not in datfile:", check_results['NIDF']),style="bold magenta")

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
