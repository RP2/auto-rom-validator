from utils.rename_utils import rename_cd_based_game_folder, rename_file


def test_rename_file(tmp_path):
    # Create a dummy file
    orig = tmp_path / "testfile.txt"
    orig.write_text("dummy")
    new_name = "renamedfile.txt"
    # Dry run should not rename
    assert rename_file(orig, new_name, dry_run=True)
    assert orig.exists()
    # Actual rename
    assert rename_file(orig, new_name)
    assert not orig.exists()
    assert (tmp_path / new_name).exists()


def test_rename_cd_based_game_folder(tmp_path):
    # Create a dummy folder
    orig = tmp_path / "game_folder"
    orig.mkdir()
    new_name = "renamed_folder"
    # Dry run should not rename
    assert rename_cd_based_game_folder(orig, new_name, dry_run=True)
    assert orig.exists()
    # Actual rename
    assert rename_cd_based_game_folder(orig, new_name)
    assert not orig.exists()
    assert (tmp_path / new_name).exists()
