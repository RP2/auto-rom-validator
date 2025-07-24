import hashlib
import zlib
from pathlib import Path
from typing import Dict, Optional, Tuple


def calculate_hash(filepath: Path, algorithm: str = "sha1") -> Optional[str]:
    """Calculate file hash with optimized chunk size for large files"""
    hash_func = hashlib.sha1() if algorithm == "sha1" else hashlib.md5()
    try:
        file_size = filepath.stat().st_size
        # Use 64KB chunk size for large files, 8KB for small files
        if file_size > 100 * 1024 * 1024:  # >100MB
            chunk_size = 65536  # 64KB
        else:
            chunk_size = 8192  # 8KB
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest().lower()
    except Exception as e:
        print(f"Error calculating hash for {filepath}: {e}")
        return None


def calculate_crc32(filepath: Path) -> Optional[str]:
    """Calculate CRC32 hash with optimized chunk size for large files"""
    crc = 0
    try:
        file_size = filepath.stat().st_size
        # Use 64KB chunk size for large files, 8KB for small files
        if file_size > 100 * 1024 * 1024:  # >100MB
            chunk_size = 65536  # 64KB
        else:
            chunk_size = 8192  # 8KB
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                crc = zlib.crc32(chunk, crc) & 0xFFFFFFFF
        return f"{crc:08x}"
    except Exception as e:
        print(f"Error calculating CRC32 for {filepath}: {e}")
        return None


def validate_file(
    filepath: Path,
    sha1_map: Dict[str, Tuple[str, str]],
    md5_map: Dict[str, Tuple[str, str]],
    crc32_map: Dict[str, Tuple[str, str]],
) -> Optional[Tuple[str, str]]:
    """Validate a single ROM file against DAT entries"""
    file_size = filepath.stat().st_size
    # For large files (>100MB), try CRC32 first as it's fastest
    if file_size > 100 * 1024 * 1024:
        crc32 = calculate_crc32(filepath)
        if crc32 and crc32 in crc32_map:
            return crc32_map[crc32]
        md5 = calculate_hash(filepath, "md5")
        if md5 and md5 in md5_map:
            return md5_map[md5]
        sha1 = calculate_hash(filepath, "sha1")
        if sha1 and sha1 in sha1_map:
            return sha1_map[sha1]
    else:
        sha1 = calculate_hash(filepath, "sha1")
        if sha1 and sha1 in sha1_map:
            return sha1_map[sha1]
        md5 = calculate_hash(filepath, "md5")
        if md5 and md5 in md5_map:
            return md5_map[md5]
        crc32 = calculate_crc32(filepath)
        if crc32 and crc32 in crc32_map:
            return crc32_map[crc32]
    return None
