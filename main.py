#!/usr/bin/env python3
"""
Simple ROM Validator
Automatically downloads DAT files and validates ROMs based on file extensions.
"""

import argparse
import sys
from pathlib import Path

from utils.config import (
    ENCRYPTION_PRONE_EXTENSIONS,
    EXTENSION_MAP,
    LIBRETRO_BASE_URL,
    PLATFORMS,
)
from utils.dat_utils import download_dat, parse_custom_dat, parse_dat
from utils.hash_utils import validate_file
from utils.platform_utils import (
    PLATFORM_ALIASES,
    guess_platform_from_file,
    infer_platform_from_folder,
)
from utils.rename_utils import rename_cd_based_game_folder, rename_file

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


def main():
    parser = argparse.ArgumentParser(description="Simple ROM Validator")
    parser.add_argument("--romdir", required=True, help="Directory containing ROM files")
    parser.add_argument("--datdir", default="./dats", help="Directory for DAT files")
    parser.add_argument(
        "--rename",
        action="store_true",
        help="Rename files to official DAT names",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without doing it",
    )
    parser.add_argument(
        "--skip-large",
        type=int,
        metavar="MB",
        help="Skip files larger than this size in MB (default: process all files)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    rom_path = Path(args.romdir)
    dat_path = Path(args.datdir)

    if not rom_path.exists():
        print(f"ROM directory does not exist: {rom_path}")
        return 1

    # Create DAT directory
    dat_path.mkdir(exist_ok=True)

    # Infer platform if running inside a single platform folder
    root_platform = infer_platform_from_folder(rom_path.name)
    if root_platform:
        print(f"Inferring single platform from folder: {root_platform}")

    # Find all ROM files and determine needed platforms
    rom_files = []
    needed_platforms = set()
    for file_path in rom_path.rglob("*"):
        if file_path.is_file():
            extension = file_path.suffix.lower()
            # Ignore CUE files as they reference BIN tracks and won't match
            if extension == ".cue":
                continue
            # Handle recognized extensions for platform detection
            if extension in EXTENSION_MAP:
                rom_files.append(file_path)
                platforms = EXTENSION_MAP[extension]
                # If root_platform is set, only include matches for that platform
                if root_platform:
                    if isinstance(platforms, list):
                        if root_platform in platforms:
                            needed_platforms.add(root_platform)
                            continue
                    else:
                        if root_platform == platforms:
                            needed_platforms.add(platforms)
                            continue
                    continue
                # Use platform utils to guess platform from file
                if isinstance(platforms, list):
                    guessed = guess_platform_from_file(file_path, EXTENSION_MAP, PLATFORM_ALIASES)
                    if guessed:
                        needed_platforms.add(guessed)
                    else:
                        for p in platforms:
                            needed_platforms.add(p)
                else:
                    needed_platforms.add(platforms)

    if not rom_files:
        print("No ROM files found with recognized extensions")
        return 1

    print(f"Found {len(rom_files)} ROM files")
    if needed_platforms:
        print(f"Detected platforms: {', '.join(sorted(needed_platforms))}")

    # Download and parse DAT files
    all_sha1_maps = {}
    all_md5_maps = {}
    all_crc32_maps = {}

    for platform in needed_platforms:
        dat_file = download_dat(platform, dat_path, PLATFORMS, LIBRETRO_BASE_URL)
        if dat_file:
            sha1_map, md5_map, crc32_map = parse_dat(dat_file)
            all_sha1_maps.update(sha1_map)
            all_md5_maps.update(md5_map)
            all_crc32_maps.update(crc32_map)
            if args.verbose:
                print(f"Loaded {len(sha1_map)} entries from {platform} DAT")

    # Load additional Encrypted/Decrypted DATs only if DS or 3DS detected
    if "Nintendo DS" in needed_platforms or "Nintendo 3DS" in needed_platforms:
        patterns = []
        if "Nintendo DS" in needed_platforms:
            patterns += [
                "*Nintendo DS*Encrypted*.dat",
                "*Nintendo DS*Decrypted*.dat",
            ]
        if "Nintendo 3DS" in needed_platforms:
            patterns += [
                "*Nintendo 3DS*Encrypted*.dat",
                "*Nintendo 3DS*Decrypted*.dat",
            ]
        for pattern in patterns:
            for extra_dat in dat_path.glob(pattern):
                sha1_map_x, md5_map_x, crc32_map_x = parse_custom_dat(extra_dat)
                all_sha1_maps.update(sha1_map_x)
                all_md5_maps.update(md5_map_x)
                all_crc32_maps.update(crc32_map_x)
                if args.verbose:
                    print(f"Loaded custom DAT '{extra_dat.name}' with {len(sha1_map_x)} entries")

    if not all_sha1_maps and not all_md5_maps and not all_crc32_maps:
        print("No DAT entries loaded")
        return 1

    # Validate ROM files
    valid_count = 0
    unknown_count = 0
    renamed_count = 0
    save_renamed_count = 0
    unknown_files = []

    # Create progress bar
    if tqdm:
        # Calculate total size for better progress estimation
        total_size = sum(f.stat().st_size for f in rom_files)
        total_size_mb = total_size / (1024 * 1024)
        print(
            f"Total data to process: {total_size_mb:.1f}MB"
        )  # Move this line before the progress bar
        iterator = tqdm(rom_files, desc="Validating", unit="file", leave=True)
    else:
        iterator = rom_files
        print("Validating files...")

    # Update the main validation loop to handle CD-based games
    for i, rom_file in enumerate(iterator):
        # Skip large files if requested
        file_size_mb = rom_file.stat().st_size / (1024 * 1024)
        if args.skip_large and file_size_mb > args.skip_large:
            if args.verbose:
                if tqdm:
                    tqdm.write(f"⏭ Skipping large file: {rom_file.name} ({file_size_mb:.1f}MB)")
                else:
                    print(f"⏭ Skipping large file: {rom_file.name} ({file_size_mb:.1f}MB)")
            continue

        # Check if the file is part of a CD-based game
        if rom_file.suffix.lower() in [".bin", ".cue"]:
            folder_path = rom_file.parent
            result = validate_file(rom_file, all_sha1_maps, all_md5_maps, all_crc32_maps)

            if result:
                rom_name, game_desc = result
                valid_count += 1

                # Handle renaming the folder
                if args.rename or args.dry_run:
                    if rename_cd_based_game_folder(folder_path, rom_name, dry_run=args.dry_run):
                        renamed_count += 1
                        if args.verbose:
                            action = "Would rename" if args.dry_run else "Renamed"
                            if tqdm:
                                tqdm.write(f"{action} folder: {folder_path.name} -> {rom_name}")
                            else:
                                print(f"{action} folder: {folder_path.name} -> {rom_name}")

                if args.verbose:
                    if tqdm:
                        tqdm.write(f"✓ {rom_file.name} -> {game_desc}")
                    else:
                        print(f"✓ {rom_file.name} -> {game_desc}")
            else:
                unknown_count += 1
                unknown_files.append(str(rom_file))
                if args.verbose:
                    if tqdm:
                        tqdm.write(f"✗ {rom_file.name} -> Unknown")
                    else:
                        print(f"✗ {rom_file.name} -> Unknown")
            continue

        result = validate_file(rom_file, all_sha1_maps, all_md5_maps, all_crc32_maps)

        if result:
            rom_name, game_desc = result
            valid_count += 1

            # Handle renaming
            if args.rename or args.dry_run:
                if rename_file(rom_file, rom_name, dry_run=args.dry_run):
                    # Rename corresponding .sav files to match the new ROM name
                    old_stem = rom_file.stem
                    new_stem = Path(rom_name).stem
                    for sav_path in rom_file.parent.rglob(f"{old_stem}.sav"):
                        new_sav = sav_path.with_name(f"{new_stem}.sav")
                        if args.dry_run:
                            # Dry-run output for save files
                            if tqdm:
                                tqdm.write(
                                    f"[Dry Run] Would rename save file: {sav_path.name} -> {new_sav.name}"
                                )
                            else:
                                print(
                                    f"[Dry Run] Would rename save file: {sav_path.name} -> {new_sav.name}"
                                )
                        else:
                            sav_path.rename(new_sav)
                            save_renamed_count += 1
                            # Verbose output for save files
                            if args.verbose:
                                if tqdm:
                                    tqdm.write(
                                        f"Renamed save file: {sav_path.name} -> {new_sav.name}"
                                    )
                                else:
                                    print(f"Renamed save file: {sav_path.name} -> {new_sav.name}")

            if args.verbose:
                # Use tqdm.write to avoid interfering with progress bar
                if tqdm:
                    tqdm.write(f"✓ {rom_file.name} -> {game_desc}")
                    # Small delay to help with progress bar display
                    import time

                    time.sleep(0.01)
                else:
                    print(f"✓ {rom_file.name} -> {game_desc}")
        else:
            unknown_count += 1
            unknown_files.append(str(rom_file))
            if args.verbose:
                # Use tqdm.write to avoid interfering with progress bar
                if tqdm:
                    tqdm.write(f"✗ {rom_file.name} -> Unknown")
                    # Small delay to help with progress bar display
                    import time

                    time.sleep(0.01)
                else:
                    print(f"✗ {rom_file.name} -> Unknown")

    # Rewrite unknown.txt each run to remove old entries
    unknown_file = Path("unknown.txt")
    with open(unknown_file, "w") as f:
        for file_path in unknown_files:
            f.write(file_path + "\n")
    if unknown_files:
        if tqdm:
            tqdm.write(f"Unknown files written to: {unknown_file}")
        else:
            print(f"Unknown files written to: {unknown_file}")
    else:
        if tqdm:
            tqdm.write(f"No unknown files. Cleared {unknown_file}.")
        else:
            print(f"No unknown files. Cleared {unknown_file}.")

    # Summary
    if tqdm:
        tqdm.write(f"\nResults: {valid_count} valid, {unknown_count} unknown")
        if renamed_count > 0:
            action = "would be renamed" if args.dry_run else "renamed"
            tqdm.write(f"Files {action}: {renamed_count}")
        if save_renamed_count > 0:
            action = "would be renamed" if args.dry_run else "renamed"
            tqdm.write(f"Save files {action}: {save_renamed_count}")

        # Check if we have encryption-prone files that didn't match
        encryption_prone_unknown = []
        for file_path in unknown_files:
            if Path(file_path).suffix.lower() in ENCRYPTION_PRONE_EXTENSIONS:
                encryption_prone_unknown.append(file_path)

        if encryption_prone_unknown:
            tqdm.write(f"\nNote: {len(encryption_prone_unknown)} DS/3DS files didn't match.")
            tqdm.write(
                "This is likely because you have encrypted ROMs, the auto downloaded No-Intro DATs list decrypted versions."
            )
            tqdm.write(
                "[!] Your files may be valid, recheck after downloading the encrypted DATs from no-intro"
            )
            tqdm.write("Link: https://datomatic.no-intro.org/index.php?page=download")
    else:
        print(f"\nResults: {valid_count} valid, {unknown_count} unknown")
        if renamed_count > 0:
            action = "would be renamed" if args.dry_run else "renamed"
            print(f"Files {action}: {renamed_count}")
        if save_renamed_count > 0:
            action = "would be renamed" if args.dry_run else "renamed"
            print(f"Save files {action}: {save_renamed_count}")
        # Check if we have encryption-prone files that didn't match
        encryption_prone_unknown = []
        for file_path in unknown_files:
            if Path(file_path).suffix.lower() in ENCRYPTION_PRONE_EXTENSIONS:
                encryption_prone_unknown.append(file_path)
        if encryption_prone_unknown:
            print(f"\nNote: {len(encryption_prone_unknown)} DS/3DS files didn't match.")
            print(
                "This is likely because you have encrypted ROMs but No-Intro DATs use decrypted versions."
            )
            print(
                "Your files may be valid and can be validated by downloading encrypted DATs from:"
            )
            print("https://datomatic.no-intro.org/index.php?page=download")

    return 0


if __name__ == "__main__":
    sys.exit(main())
