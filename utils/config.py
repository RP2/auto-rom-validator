# config.py
"""Configuration for ROM Validator"""

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

EXTENSION_MAP = {
    '.gba': 'Game Boy Advance',
    '.gb': 'Game Boy',
    '.gbc': 'Game Boy Color',
    # DS-based ROMs map to multiple DATs
    '.nds': ['Nintendo DS', 'Nintendo DS Download Play', 'Nintendo DSi'],
    '.3ds': 'Nintendo 3DS',
    # Disc images: all platforms that use .iso
    '.iso': ['GameCube', 'PSP', 'PlayStation 2', 'Wii'],
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

ENCRYPTION_PRONE_EXTENSIONS = {'.nds', '.3ds'}
