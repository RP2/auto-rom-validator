from typing import Dict, List, Optional
from pathlib import Path

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

def infer_platform_from_folder(folder_name: str) -> Optional[str]:
    """Infer platform from folder name using aliases."""
    folder_name = folder_name.lower().replace(' ', '')
    for plat, aliases in PLATFORM_ALIASES.items():
        for alias in aliases:
            if alias in folder_name:
                return plat
    return None

def guess_platform_from_file(file_path: Path, extension_map: Dict[str, str], platform_aliases: Dict[str, List[str]]) -> Optional[str]:
    """Guess platform from file extension and parent folder name."""
    ext = file_path.suffix.lower()
    if ext in extension_map:
        platforms = extension_map[ext]
        if isinstance(platforms, list):
            parent_name = file_path.parent.name.lower().replace(' ', '')
            for p in platforms:
                aliases = platform_aliases.get(p, [p.lower().replace(' ', '')])
                for alias in aliases:
                    if alias in parent_name:
                        return p
            return platforms[0]  # fallback
        else:
            return platforms
    return None
