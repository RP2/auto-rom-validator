import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests


def download_dat(platform: str, dat_dir: Path, platforms: dict, base_url: str) -> Optional[Path]:
    """Download DAT file for a platform"""
    if platform not in platforms:
        return None
    url = f"{base_url}/{platforms[platform]}"
    dat_path = Path(dat_dir) / f"{platform}.dat"
    if dat_path.exists():
        return dat_path
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(dat_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        return dat_path
    except Exception as e:
        print(f"Failed to download DAT for {platform}: {e}")
        return None


def parse_dat(
    dat_path: Path,
) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, Tuple[str, str]], Dict[str, Tuple[str, str]]]:
    """Parse clrmamepro DAT file and return hash maps"""
    sha1_map = {}
    md5_map = {}
    crc32_map = {}
    try:
        with open(dat_path, "r", encoding="utf-8") as f:
            content = f.read()
        game_sections = content.split("game (")[1:]
        for game_section in game_sections:
            paren_count = 1
            game_end = 0
            for i, char in enumerate(game_section):
                if char == "(":
                    paren_count += 1
                elif char == ")":
                    paren_count -= 1
                    if paren_count == 0:
                        game_end = i
                        break
            if game_end == 0:
                continue
            game_content = game_section[:game_end]
            desc_match = re.search(r'description\s+"([^"]*)"', game_content)
            game_desc = desc_match.group(1) if desc_match else "Unknown"
            rom_lines = [
                line.strip() for line in game_content.split("\n") if "rom (" in line and ")" in line
            ]
            for rom_line in rom_lines:
                name_match = re.search(r'name\s+"([^"]*)"', rom_line)
                rom_name = name_match.group(1) if name_match else "Unknown"
                sha1_match = re.search(r"sha1\s+([A-Fa-f0-9]+)", rom_line)
                md5_match = re.search(r"md5\s+([A-Fa-f0-9]+)", rom_line)
                crc_match = re.search(r"crc\s+([A-Fa-f0-9]+)", rom_line)
                if sha1_match:
                    sha1_map[sha1_match.group(1).lower()] = (
                        rom_name, game_desc)
                if md5_match:
                    md5_map[md5_match.group(1).lower()] = (rom_name, game_desc)
                if crc_match:
                    crc32_map[crc_match.group(1).lower()] = (
                        rom_name, game_desc)
    except Exception as e:
        print(f"Error parsing DAT file {dat_path}: {e}")
    return sha1_map, md5_map, crc32_map


def parse_custom_dat(
    dat_path: Path,
) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, Tuple[str, str]], Dict[str, Tuple[str, str]]]:
    """Parse alternative DAT files (XML layout) and return hash maps"""
    sha1_map = {}
    md5_map = {}
    crc32_map = {}
    try:
        tree = ET.parse(dat_path)
        root = tree.getroot()
        for game in root.findall("game"):
            game_desc = game.get("description") or game.get("name", "Unknown")
            for rom in game.findall("rom"):
                rom_name = rom.get("name", "Unknown")
                sha1 = rom.get("sha1")
                md5 = rom.get("md5")
                crc = rom.get("crc")
                if sha1:
                    sha1_map[sha1.lower()] = (rom_name, game_desc)
                if md5:
                    md5_map[md5.lower()] = (rom_name, game_desc)
                if crc:
                    crc32_map[crc.lower()] = (rom_name, game_desc)
    except Exception as e:
        print(f"Error parsing custom DAT file {dat_path}: {e}")
    return sha1_map, md5_map, crc32_map
