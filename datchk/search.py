"""
DATCHK
A command line datfile parser and rom validator written in python.

Written By: Daws
"""

from rich.table import Table


class Search:
    def __init__(self, console, dat):
        self.console = console
        self.dat = dat
        self.results: dict = {}

    def build_results_table(self):
        table = Table(title="Search Results", show_lines=True)
        table.add_column("ID", justify="center", style="bold red", width=4)
        table.add_column("Title")
        table.add_column("MD5", justify="right", style="green")

        for idx, name in self.results.items():
            table.add_row(
                str(idx), str(name), str(self.dat.get_md5_from_name_exact(name))
            )

        return table

    def search(self, search_key):
        self.results = self.dat.search_rom_names_w_str(search_key)
        self.show()

    def show(self):
        if self.results:
            self.console.print(
                "[!] Found {} matching entries..\n".format(len(self.results)),
                style="bold yellow",
            )

            self.console.print(self.build_results_table())

            while True:
                selection = input("\nSelection (q to QUIT): ")
                if selection.isdigit() and int(selection) <= len(self.results) - 1:
                    self.dat.get_rom_node_from_name_exact(self.results[int(selection)])
                    self.dat.print_current_rom_data()

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
                    self.console.print("[-] Invalid selection", style="bold red")
                    continue
        else:
            self.console.print("[!] No results", style="bold yellow")
