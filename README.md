# datchk
Command line datfile parser and validator

# Installation
```
git clone https://github.com/0xDAWS/datchk.git
cd datchk
pip install .
```

# Usage
### Search the dat file using keywords
```
datchk --datfile path/to/datfile.dat --search "Zelda"
```
Note: **Search** feature is currently a WIP and has trouble with finding results when given multiple keywords. The best way to use it in the current state is single keywords such as "Mario", "Banjo" or even a region like "USA" or "Japan". 

### Perform check on a rom or directory of roms
```
datchk --datfile path/to/datfile.dat --check path/to/roms
```

### Perform check but only show failed results
```
datchk --datfile path/to/datfile.dat --check --failed path/to/roms
```
Failed results contain not only failed checksums (FAIL), but also CheckSum Not Available (CSNA) and Not In DatFile (NIDF) results. Read [Output Codes](#output-codes) for more

### Perform check but use hash algorithm other than md5
```
datchk --datfile path/to/datfile.dat --check --algorithm sha256 path/to/roms
```
In most cases MD5 is perfectly fine for checking the integrity of a file since we don't require any particular cryptographic strength for the use of verifying the file bytes are correct. Nevertheless some users may want to use other hash algorithms commonly found in datfiles, so several are made available.

**Available algorithms: MD5, SHA1, SHA256**

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
Some of th output codes (acronyms in square brackets) will be self explanatory, but let's take a look at what each means and how it can help you to get the best information from the check results.

### PASS
The file matched an entry in the datfile and it's checksum was validated as correct.

### FAIL
When comparing checksums, a match will give a **PASS** result as mentioned above, but an incorrect match will give the **FAIL** result. Fail in this case means the rom entry was correctly identified in the datfile, but the checksum of the rom does not match the corresponding value in the datfile entry.

### CSNA (CheckSum Not Available)
Some datfile entries are missing SHA1 and SHA256 checksums. We don't require cryptographically secure algorithms for this task, so an MD5 digest is usually enough to verify the file is intact and correct. In a check operation, if an entry is missing the checksum for the chosen algorithm, the check output for that entry will be marked as **CSNA**.

### NIDF (Not In DatFile)
Datchk attempts to locate matching entries in a datfile by using the exact name of the entry first and the MD5 digest second. If neither of these options are able to locate the entry it is marked as **NIDF**. The NIDF fail type shows that your file could be incorrectly named **AND** that the MD5 digest doesn't match, so an entry could not be found in the datfile.

### PBIN (Pass But Incorrect Name)
This code shows that the MD5 of the file currently being processed *was* located in the datfile, but the name of the file did not match the corresponding value in the datfile entry. Essentially you have a valid file, but an incorrect name. Often worth investigating to ensure the filename matches it's contents.

*You should take note of the filename inside the brackets, this is the name which contains the matching MD5 entry in the datfile, and will be useful in identifying if the rom is adequately named*

# GPG Signing Key
All official releases are signed with my GPG key found [here](https://github.com/0xDAWS/Public-Keys/blob/main/0xDAWS.SigningKey.Public.asc)

You can verify the downloaded files are intact and unmodified by verifying the checksum file using this key.
