"""
DATCHK
A command line datfile parser and rom validator written in python.

Written By: Daws
"""

import hashlib
from pathlib import Path
from py7zr import SevenZipFile
from zipfile import ZipFile

CHUNK_SIZE = 16 * 1024


def extract_archive(rom_path, tmpdir) -> str:
    if Path(rom_path).suffix == ".zip":
        with ZipFile(rom_path, "r") as z:
            rom_name = z.namelist()[0]
            z.extract(rom_name, tmpdir.name)

    elif Path(rom_path).suffix == ".7z":
        with SevenZipFile(rom_path, "r") as z:
            rom_name = z.files.files_list[0]["filename"]
            z.extract(path=tmpdir.name)

    return rom_name


class HashHandler:
    def __init__(self) -> None:
        self.read_bytes: int = 0
        self.status: str = ""
        # self.tmp_dir = tmpdir
        # self.progress = pbar
        # self.task = task

    def get_digest(self, rom, algo) -> str:
        h = hashlib.new(algo)
        # self.progress.update(self.task, completed=0)

        with open(rom, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                h.update(chunk)
                self.read_bytes += len(chunk)

        return h.hexdigest()

    def compare_checksum(self, rom, digest, algo) -> bool:
        return self.get_digest(rom, algo) == digest

    def get_read_bytes(self) -> int:
        return self.read_bytes

    def get_status(self) -> str:
        return self.status
