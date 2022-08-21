# Datchk - Datfile Checker
A command line datfile parser and rom validator written in python.

# Quick Links
- [Installation](#installation)
- [Usage](#usage)
- [Supported File Types](#supported-file-types)
- [Output Codes](#output-codes)
- [GPG Key](#gpg-signing-key)
- [Planned Features](#planned-features)

# Installation
```
git clone https://github.com/0xDAWS/datchk.git
cd datchk
pip install .
```

# Usage

### Perform check on a rom or directory of roms
```
datchk --datfile path/to/datfile.dat --check path/to/roms
```
___

### Perform check but only show failed results
```
datchk --datfile path/to/datfile.dat --check --failed path/to/roms
```

**NOTE:** Failed results contain not only failed checksums (FAIL), but also CheckSum Not Available (CSNA) and Not In DatFile (NIDF) results. Read [Output Codes](#output-codes) for more
___

### Perform check but use hash algorithm other than md5
```
datchk --datfile path/to/datfile.dat --check --algorithm sha256 path/to/roms
```
In most cases MD5 is perfectly fine for checking the integrity of a file since we don't require any particular cryptographic strength for the use of verifying the file bytes are correct. Nevertheless some users may want to use other hash algorithms commonly found in datfiles, so several are made available.

**Available algorithms: MD5, SHA1, SHA256**
___

### Search the dat file using keywords
**NOTE:** Searching is currently a WIP and can have trouble with finding results when  multiple keywords are used without proper order. Currently it uses a simple string comparison to match keywords with datfile entries, so it will not find results that are 

The best search terms would be simple, singular keywords such as "Mario", "Banjo", "Ocarina" or even a region like "USA" or "Japan". These will be easily located in the datfile, and a numbered list containing all matching entries will be displayed. You can then select an entry by it's index to see all the information available for that entry.

The search feature can match long and complex strings however, if they match a title **exactly**.
```
datchk --datfile path/to/datfile.dat --search "Zelda"
```

# Supported file types
The best way to use [datchk](#datchk) is to have your roms uncompressed and organised in suitable directories. Some users prefer to have their roms compressed to save disk space, so datchk can process and validate compressed roms as well!

To achieve this the compressed archive will be decompressed to a tmp directory created when you execute datchk. Obviously, this will result in more read/writes on your disk and will be much slower in most cases, so it's a better idea to have your roms uncompressed for the best experience.

**Supported archive formats: .zip and .7z**

Archive files must contain **ONLY** a single rom to be processed by datchk, multiple file archives are not supported.

# Output Codes
Typical output from using the check flag will look something like this

```
❯ datchk -d path/to/datfile.dat -c path/to/roms
[+] Started check operation..
[ PASS ]  rom-1.ext
[ FAIL ]  rom-2.ext
[ CSNA ]  rom-3.ext
[ NIDF ]  rom-4.ext
[ PBIN ]  rom-5.ext (Legend of Rom - Rom's Adventure.ext)
```
Some of the output codes will be self explanatory, but let's take a look at what each means and how it can help you to get the best information from the check results.

### PASS
The file matched an entry in the datfile and it's checksum was validated as correct.
___

### FAIL
When comparing checksums, a match will give a **PASS** result as mentioned above, but an incorrect match will give the **FAIL** result. Fail in this case means the rom entry was correctly identified in the datfile, but the checksum of the rom does not match the corresponding value in the datfile entry.
___

### CSNA (CheckSum Not Available)
Some datfile entries are missing SHA1 and SHA256 checksums. We don't require cryptographically secure algorithms for this task, so an MD5 digest is usually enough to verify the file is intact and correct. In a check operation, if an entry is missing the checksum for the chosen algorithm, the check output for that entry will be marked as **CSNA**.
___

### NIDF (Not In DatFile)
Datchk attempts to locate matching entries in a datfile by using the exact name of the entry first and the MD5 digest second. If neither of these options are able to locate the entry it is marked as **NIDF**. The NIDF fail type shows that your file could be incorrectly named **AND** that the MD5 digest doesn't match, so an entry could not be found in the datfile.
___

### PBIN (Pass But Incorrect Name)
This code shows that the MD5 of the file currently being processed *was* located in the datfile, but the name of the file did not match the corresponding value in the datfile entry. Essentially you have a valid file, but an incorrect name. Often worth investigating to ensure the filename matches it's contents.

*You should take note of the filename inside the brackets, this is the name of the entry in the datfile which matches the MD5 checksum of your file. It's useful for finding valid but incorrectly named roms.*

# GPG Signing Key
All official releases are signed with my GPG key found [here](https://github.com/0xDAWS/Public-Keys/blob/main/0xDAWS.SigningKey.Public.asc)

You can verify the downloaded files are intact and unmodified by verifying the checksum file using this key.

# Planned features
- Improve search functionality and output formatting
- Allow users to generate a list from search results (All titles for a specific region for example)
- Implement auto-rename, which will allow users to rename files which have a different name from their entry in the datfile.
- More error handling
- Progress bar/counter