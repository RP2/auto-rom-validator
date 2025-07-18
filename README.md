# Auto ROM Validator

A Python script to validate and standardize your ROM backup collection using official No-Intro and Redump DAT files.

On startup, the script reports:

```text
Found <N> ROM files
Detected platforms: <Platform1>, <Platform2>, ...
```

## Features

- **DAT Fetching:** Automatically downloads DATs for supported platforms.
- **Custom DAT Support:** Parses extra encrypted/decrypted DAT files placed in `dats/` (XML layout).
- **Multi-Hash Validation:** Checks files using SHA1, MD5, and CRC32.
- **Folder Awareness:** Suggests or renames platform folders based on file contents.
- **File & Folder Renaming:** Standardizes filenames and CD-based game folders (`.bin`/`.cue`).
- **Unknowns List:** Maintains `unknown.txt`, rewriting it each run to clear old entries.
- **Progress Bars:** Shows per-file progress with `tqdm` if installed.
- **Verbose Mode:** Detailed per-file output with `--verbose`.
- **Dry Run:** Preview renames without applying with `--dry-run`.
- **Large File Handling:** Skip or prioritize large files via `--skip-large <MB>`.

## Usage

```bash
python auto_validate_roms.py --romdir /path/to/ROMS [options]
```

## Options

- `--romdir <path>`: Directory containing ROM files (required).
- `--datdir <path>`: Directory for DAT files (default: `./dats`).
- `--rename`: Rename files and folders to official DAT names.
- `--dry-run`: Preview renames without making changes.
- `--skip-large <MB>`: Skip files larger than this size in megabytes.
- `--verbose`, `-v`: Enable verbose output.

## Example Output

```text
Found 120 ROM files
Detected platforms: Game Boy, Nintendo DS, PlayStation
Validating files:  75%|███████▏   | 90/120 [00:30<00:10, 3.0file/s]
✓ Mario Kart DS -> Mario Kart DS (USA)
✗ RandomHack.nds -> Unknown
Unknown files written to: unknown.txt

Results: 45 valid, 1 unknown
Files renamed: 10
```

If DS/3DS encryption mismatches occur, it will note:

```text
Note: 2 DS/3DS files didn't match.
Encrypted ROMs require encrypted DATs.
Download them from:
https://datomatic.no-intro.org/index.php?page=download
```

## Requirements

- Python 3.7+
- `requests` (`pip install requests`)
- Optional: `tqdm` for progress bars (`pip install tqdm`)

## License

This project is licensed under the [MIT License](LICENSE).
