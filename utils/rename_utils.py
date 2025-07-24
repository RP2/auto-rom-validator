from pathlib import Path


def rename_file(old_path: Path, new_name: str, dry_run: bool = False) -> bool:
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


def rename_cd_based_game_folder(
    folder_path: Path, new_name: str, dry_run: bool = False
) -> bool:
    """Rename a folder containing CD-based game files to the official DAT name"""
    folder_path = Path(folder_path)
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
