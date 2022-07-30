import hashlib
from pathlib import Path
from py7zr import SevenZipFile
from zipfile import ZipFile


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


def get_digest(algorithm, rom_path, tmp_dir) -> str:
    h = hashlib.new(algorithm)

    if Path(rom_path).suffix in [".zip", ".7z"]:
        rom_name = extract_archive(rom_path, tmp_dir)

        with open(Path(tmp_dir.name, rom_name), "rb") as f:
            h.update(f.read())

    else:
        with open(rom_path, "rb") as f:
            h.update(f.read())

    return h.hexdigest()


def compare_checksum(rom_path, rom_digest, algoritm, tmpdir) -> bool:
    return get_digest(algoritm, rom_path, tmpdir) == rom_digest
