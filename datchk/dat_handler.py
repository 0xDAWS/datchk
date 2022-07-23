from dataclasses import dataclass
from pathlib import Path
from rich.console import Console
from rich.table import Table
import xml.etree.ElementTree as xml

@dataclass
class Rom:
    name:   str
    size:   str
    crc:    str
    md5:    str
    sha1:   str
    sha256: str
    serial: str
    status: str

class DatParser(object):
    def __init__(self, infile):
        self.datfile = infile
        self.tree = xml.parse(self.datfile)
        self.root = self.tree.getroot()
        self.games  = self.root.findall('game')
        self.entries = len(self.games)
        self.current_rom = Rom
        self.current_rom_found_match = False
        self.console = Console()

    def get_dat_header(self):
        return [t.tag for t in self.header[0]]
	
	def search_rom_names_w_str(self, search_key: str) -> list:
        entry_idx = 0
        
        keys = [search_key,
                search_key.lower(),
                search_key.upper(),
                search_key.title(),
                search_key.capitalize()]

        results = {}
        for game in self.games:
            for key in keys:
                if key in game.get('name'):
                    if game.find('rom').get('name') not in results.values():
                        results[entry_idx] = game.find('rom').get('name')
                        entry_idx+=1
                    else:
                        pass

        return results
	
	def get_rom_node_from_name_exact(self, rom_name: str):
        for e in self.root.findall(f'game[@name="{Path(rom_name).stem}"]'):
            for rom_data in e.findall(f'rom'):
                if rom_data.get('name') is not None:
                    self.current_rom_found_match = True
                    self.parse_game_node(rom_data)
                    return
				
	def get_rom_node_from_md5(self, digest: str):
        for e in self.root.iterfind(f'game/rom[@md5="{digest}"]'):
            if e.get('md5') is not None:
                self.current_rom_found_match = True
                self.parse_game_node(e)
                return

    def get_md5_from_name_exact(self, rom_name: str):
        for e in self.root.findall(f'game/rom[@name="{rom_name}"]'):
            return e.get('md5')
        
    def parse_game_node(self, game_node):
        if game_node is not None:
            try:
                self.current_rom.name        = game_node.get('name')
                self.current_rom.size        = game_node.get('size')
                self.current_rom.crc         = game_node.get('crc')
                self.current_rom.md5         = game_node.get('md5')
                self.current_rom.sha1        = game_node.get('sha1')
                self.current_rom.sha256      = game_node.get('sha256')
                self.current_rom.serial      = game_node.get('serial')
                self.current_rom.status      = game_node.get('status')

            except AttributeError as e:
                print("[ERROR] Problem processing with the provided information")
        
        else:
            print("[NO DATA] There was an issue parsing rom data with the supplied flags")
            pass
        
    def print_current_rom_data(self):
        self.console.rule(self.current_rom.name)

        table = Table(show_lines=True)

        table.add_column("Attribute")
        table.add_column("Value")

        table.add_row("Size", self.current_rom.size)
        table.add_row("CRC", self.current_rom.crc)
        table.add_row("MD5", self.current_rom.md5)
        table.add_row("SHA1", self.current_rom.sha1)
        table.add_row("SHA256", self.current_rom.sha256)
        table.add_row("Serial", self.current_rom.serial)
        table.add_row("Status", self.current_rom.status)

        self.console.print(table)
