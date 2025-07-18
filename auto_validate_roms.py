#!/usr/bin/env python3
"""
Simple ROM Validator
Automatically downloads DAT files and validates ROMs based on file extensions.
"""

import os
import sys
import hashlib
import requests
import re
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Configuration
LIBRETRO_BASE_URL = "https://raw.githubusercontent.com/libretro/libretro-database/master"
PLATFORMS = {
    "Game Boy Advance": "metadat/no-intro/Nintendo - Game Boy Advance.dat",
    "Game Boy": "metadat/no-intro/Nintendo - Game Boy.dat", 
    "Game Boy Color": "metadat/no-intro/Nintendo - Game Boy Color.dat",
    "Nintendo DS": "metadat/no-intro/Nintendo - Nintendo DS.dat",
    "Nintendo DS Download Play": "metadat/no-intro/Nintendo - Nintendo DS (Download Play).dat",
    "Nintendo DSi": "metadat/no-intro/Nintendo - Nintendo DSi.dat",
    "Nintendo 3DS": "metadat/no-intro/Nintendo - Nintendo 3DS.dat",
    "PlayStation": "metadat/redump/Sony - PlayStation.dat",
    "PlayStation 2": "metadat/redump/Sony - PlayStation 2.dat",
    "PSP": "metadat/no-intro/Sony - PlayStation Portable.dat",
    "GameCube": "metadat/redump/Nintendo - GameCube.dat",
    "Wii": "metadat/redump/Nintendo - Wii.dat"
}

# File extension to platform mapping
EXTENSION_MAP = {
    '.gba': 'Game Boy Advance',
    '.gb': 'Game Boy',
    '.gbc': 'Game Boy Color',
    # DS-based ROMs map to multiple DATs
    '.nds': ['Nintendo DS', 'Nintendo DS Download Play', 'Nintendo DSi'],
    '.3ds': 'Nintendo 3DS',
    # Disc images: PSP and PS2 both use .iso
    '.iso': ['PSP', 'PlayStation 2', 'Wii'],
    '.cso': 'PSP',
    '.pbp': 'PSP',
    # GameCube image formats
    '.gcm': 'GameCube',
    '.ciso': 'GameCube',
    # Wii image format
    '.wbfs': 'Wii',
    # CD-based: PS1 and PS2 may use .bin/.cue
    '.psx': 'PlayStation',
    '.cue': ['PlayStation', 'PlayStation 2'],
    '.bin': ['PlayStation', 'PlayStation 2'],
}

# Extensions that commonly have encryption issues
ENCRYPTION_PRONE_EXTENSIONS = {'.nds', '.3ds'}

# Aliases for inferring platform from folder names
PLATFORM_ALIASES = {
    'PlayStation': ['ps1', 'psx', 'playstation'],
    'PlayStation 2': ['ps2', 'playstation2'],
    'PSP': ['psp'],
    'Wii': ['wii'],
    'GameCube': ['gamecube', 'gcm', 'ciso'],
    'Nintendo DS': ['nds', 'nintendods', 'nintendo-ds'],
    'Nintendo DSi': ['dsi', 'nintendodsi'],
    'Nintendo DS Download Play': ['downloadplay', 'ndsd', 'dsdownload'],
    'Nintendo 3DS': ['3ds', 'nintendo3ds']
}

def download_dat(platform, dat_dir):
    """Download DAT file for a platform"""
    if platform not in PLATFORMS:
        return None
        
    url = f"{LIBRETRO_BASE_URL}/{PLATFORMS[platform]}"
    dat_path = Path(dat_dir) / f"{platform}.dat"
    
    if dat_path.exists():
        return dat_path
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(dat_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return dat_path
    except Exception as e:
        print(f"Failed to download DAT for {platform}: {e}")
        return None

def parse_dat(dat_path):
    """Parse clrmamepro DAT file and return hash maps"""
    sha1_map = {}
    md5_map = {}
    crc32_map = {}
    
    try:
        with open(dat_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by "game (" to get individual game sections
        game_sections = content.split('game (')[1:]  # Skip the first part (header)
        
        for game_section in game_sections:
            # Find the closing parenthesis for this game
            paren_count = 1
            game_end = 0
            for i, char in enumerate(game_section):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        game_end = i
                        break
            
            if game_end == 0:
                continue
            
            game_content = game_section[:game_end]
            
            # Get game description
            desc_match = re.search(r'description\s+"([^"]*)"', game_content)
            game_desc = desc_match.group(1) if desc_match else "Unknown"
            
            # Find ROM entries - they're on single lines
            rom_lines = []
            for line in game_content.split('\n'):
                if 'rom (' in line and ')' in line:
                    rom_lines.append(line.strip())
            
            for rom_line in rom_lines:
                # Extract ROM name and hashes
                name_match = re.search(r'name\s+"([^"]*)"', rom_line)
                rom_name = name_match.group(1) if name_match else "Unknown"
                
                sha1_match = re.search(r'sha1\s+([A-Fa-f0-9]+)', rom_line)
                md5_match = re.search(r'md5\s+([A-Fa-f0-9]+)', rom_line)
                crc_match = re.search(r'crc\s+([A-Fa-f0-9]+)', rom_line)
                
                if sha1_match:
                    sha1_map[sha1_match.group(1).lower()] = (rom_name, game_desc)
                if md5_match:
                    md5_map[md5_match.group(1).lower()] = (rom_name, game_desc)
                if crc_match:
                    crc32_map[crc_match.group(1).lower()] = (rom_name, game_desc)
    
    except Exception as e:
        print(f"Error parsing DAT file {dat_path}: {e}")
    
    return sha1_map, md5_map, crc32_map

def parse_custom_dat(dat_path):
    """Parse alternative DAT files (XML layout) and return hash maps"""
    sha1_map = {}
    md5_map = {}
    crc32_map = {}
    try:
        tree = ET.parse(dat_path)
        root = tree.getroot()
        for game in root.findall('game'):
            game_desc = game.get('description') or game.get('name', 'Unknown')
            for rom in game.findall('rom'):
                rom_name = rom.get('name', 'Unknown')
                sha1 = rom.get('sha1')
                md5 = rom.get('md5')
                crc = rom.get('crc')
                if sha1:
                    sha1_map[sha1.lower()] = (rom_name, game_desc)
                if md5:
                    md5_map[md5.lower()] = (rom_name, game_desc)
                if crc:
                    crc32_map[crc.lower()] = (rom_name, game_desc)
    except Exception as e:
        print(f"Error parsing custom DAT file {dat_path}: {e}")
    return sha1_map, md5_map, crc32_map

def calculate_hash(filepath, algorithm="sha1"):
    """Calculate file hash with optimized chunk size for large files"""
    hash_func = hashlib.sha1() if algorithm == "sha1" else hashlib.md5()
    
    try:
        file_size = filepath.stat().st_size
        # Use larger chunk size for files > 100MB
        chunk_size = 65536 if file_size > 100 * 1024 * 1024 else 8192
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest().lower()
    except Exception as e:
        print(f"Error calculating hash for {filepath}: {e}")
        return None

def calculate_crc32(filepath):
    """Calculate CRC32 hash with optimized chunk size for large files"""
    import zlib
    crc = 0
    try:
        file_size = filepath.stat().st_size
        # Use larger chunk size for files > 100MB  
        chunk_size = 65536 if file_size > 100 * 1024 * 1024 else 8192
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                crc = zlib.crc32(chunk, crc) & 0xffffffff
        return f"{crc:08x}"
    except Exception as e:
        print(f"Error calculating CRC32 for {filepath}: {e}")
        return None

def validate_file(filepath, sha1_map, md5_map, crc32_map):
    """Validate a single ROM file against DAT entries"""
    file_size = filepath.stat().st_size
    
    # For large files (>100MB), try CRC32 first as it's fastest
    if file_size > 100 * 1024 * 1024:
        # Try CRC32 first for large files
        crc32 = calculate_crc32(filepath)
        if crc32 and crc32 in crc32_map:
            return crc32_map[crc32]
        
        # Try MD5 next (faster than SHA1)
        md5 = calculate_hash(filepath, "md5")
        if md5 and md5 in md5_map:
            return md5_map[md5]
        
        # Try SHA1 last
        sha1 = calculate_hash(filepath, "sha1")
        if sha1 and sha1 in sha1_map:
            return sha1_map[sha1]
    else:
        # For small files, use original order
        # Try SHA1 first
        sha1 = calculate_hash(filepath, "sha1")
        if sha1 and sha1 in sha1_map:
            return sha1_map[sha1]
        
        # Try MD5
        md5 = calculate_hash(filepath, "md5")
        if md5 and md5 in md5_map:
            return md5_map[md5]
        
        # Try CRC32
        crc32 = calculate_crc32(filepath)
        if crc32 and crc32 in crc32_map:
            return crc32_map[crc32]
    
    return None

def rename_file(old_path, new_name, dry_run=False):
    """Rename a file to the official DAT name"""
    old_path = Path(old_path)
    new_path = old_path.parent / new_name
    
    if old_path == new_path:
        return False
    
    if new_path.exists():
        return False
    
    if not dry_run:
        old_path.rename(new_path)
    
    return True

def rename_cd_based_game_folder(folder_path, new_name, dry_run=False):
    """Rename a folder containing CD-based game files to the official DAT name"""
    folder_path = Path(folder_path)
    # Remove file extension from the new name
    new_name = Path(new_name).stem
    new_path = folder_path.parent / new_name

    if folder_path == new_path:
        return False

    if new_path.exists():
        return False

    if dry_run:
        print(f"[Dry Run] Would rename folder: {folder_path} -> {new_path}")
    else:
        folder_path.rename(new_path)

    return True

def main():
    parser = argparse.ArgumentParser(description='Simple ROM Validator')
    parser.add_argument('--romdir', required=True, help='Directory containing ROM files')
    parser.add_argument('--datdir', default='./dats', help='Directory for DAT files')
    parser.add_argument('--rename', action='store_true', help='Rename files to official DAT names')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without doing it')
    parser.add_argument('--skip-large', type=int, metavar='MB', help='Skip files larger than this size in MB (default: process all files)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    rom_path = Path(args.romdir)
    dat_path = Path(args.datdir)
    
    if not rom_path.exists():
        print(f"ROM directory does not exist: {rom_path}")
        return 1
    
    # Create DAT directory
    dat_path.mkdir(exist_ok=True)
    
    # Infer platform if running inside a single platform folder
    root_name = rom_path.name.lower().replace(' ', '')
    root_platform = None
    for plat, aliases in PLATFORM_ALIASES.items():
        for alias in aliases:
            if alias in root_name:
                root_platform = plat
                break
        if root_platform:
            print(f"Inferring single platform from folder: {root_platform}")
            break

    # Find all ROM files and determine needed platforms
    rom_files = []
    needed_platforms = set()
    
    for file_path in rom_path.rglob('*'):
        if file_path.is_file():
            extension = file_path.suffix.lower()
            # Ignore CUE files as they reference BIN tracks and won't match
            if extension == '.cue':
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
                    # Skip files that don't match root platform
                    continue

                # Support list mappings by guessing via folder name
                if isinstance(platforms, list):
                    # Try to infer platform from parent folder
                    parent_name = file_path.parent.name.lower().replace(' ', '')
                    guessed = None
                    for p in platforms:
                        aliases = PLATFORM_ALIASES.get(p, [p.lower().replace(' ', '')])
                        for alias in aliases:
                            if alias in parent_name:
                                guessed = p
                                break
                        if guessed:
                            break
                    if guessed:
                        needed_platforms.add(guessed)
                    else:
                        # Fallback: load all possible platforms
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
        dat_file = download_dat(platform, dat_path)
        if dat_file:
            sha1_map, md5_map, crc32_map = parse_dat(dat_file)
            all_sha1_maps.update(sha1_map)
            all_md5_maps.update(md5_map)
            all_crc32_maps.update(crc32_map)
            if args.verbose:
                print(f"Loaded {len(sha1_map)} entries from {platform} DAT")
    
    # Load additional Encrypted/Decrypted DATs only if DS or 3DS detected
    if 'Nintendo DS' in needed_platforms or 'Nintendo 3DS' in needed_platforms:
        patterns = []
        if 'Nintendo DS' in needed_platforms:
            patterns += ["*Nintendo DS*Encrypted*.dat", "*Nintendo DS*Decrypted*.dat"]
        if 'Nintendo 3DS' in needed_platforms:
            patterns += ["*Nintendo 3DS*Encrypted*.dat", "*Nintendo 3DS*Decrypted*.dat"]
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
    unknown_files = []
    
    # Create progress bar
    if tqdm:
        # Calculate total size for better progress estimation
        total_size = sum(f.stat().st_size for f in rom_files)
        total_size_mb = total_size / (1024 * 1024)
        print(f"Total data to process: {total_size_mb:.1f}MB")  # Move this line before the progress bar
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
        if rom_file.suffix.lower() in ['.bin', '.cue']:
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
                    renamed_count += 1
                    if args.verbose:
                        action = "Would rename" if args.dry_run else "Renamed"
                        # Use tqdm.write to avoid interfering with progress bar
                        if tqdm:
                            tqdm.write(f"{action}: {rom_file.name} -> {rom_name}")
                            # Small delay to help with progress bar display
                            import time
                            time.sleep(0.01)
                        else:
                            print(f"{action}: {rom_file.name} -> {rom_name}")
            
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
    with open(unknown_file, 'w') as f:
        for file_path in unknown_files:
            f.write(file_path + '\n')
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
        
        # Check if we have encryption-prone files that didn't match
        encryption_prone_unknown = []
        for file_path in unknown_files:
            if Path(file_path).suffix.lower() in ENCRYPTION_PRONE_EXTENSIONS:
                encryption_prone_unknown.append(file_path)
        
        if encryption_prone_unknown:
            tqdm.write(f"\nNote: {len(encryption_prone_unknown)} DS/3DS files didn't match.")
            tqdm.write("This is likely because you have encrypted ROMs, the auto downloaded No-Intro DATs list decrypted versions.")
            tqdm.write("[!] Your files may be valid, recheck after downloading the encrypted DATs from no-intro")
            tqdm.write("Link: https://datomatic.no-intro.org/index.php?page=download")
    else:
        print(f"\nResults: {valid_count} valid, {unknown_count} unknown")
        if renamed_count > 0:
            action = "would be renamed" if args.dry_run else "renamed"
            print(f"Files {action}: {renamed_count}")
        # Check if we have encryption-prone files that didn't match
        encryption_prone_unknown = []
        for file_path in unknown_files:
            if Path(file_path).suffix.lower() in ENCRYPTION_PRONE_EXTENSIONS:
                encryption_prone_unknown.append(file_path)
        if encryption_prone_unknown:
            print(f"\nNote: {len(encryption_prone_unknown)} DS/3DS files didn't match.")
            print("This is likely because you have encrypted ROMs but No-Intro DATs use decrypted versions.")
            print("Your files may be valid and can be validated by downloading encrypted DATs from:")
            print("https://datomatic.no-intro.org/index.php?page=download")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
