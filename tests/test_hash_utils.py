from utils.hash_utils import calculate_crc32, calculate_hash


def test_calculate_hash(tmp_path):
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"abc123")
    assert (
        calculate_hash(test_file, "md5") == "e99a18c428cb38d5f260853678922e03"
    )
    assert (
        calculate_hash(test_file, "sha1")
        == "6367c48dd193d56ea7b0baad25b19455e529f5ee"
    )


def test_calculate_crc32(tmp_path):
    test_file = tmp_path / "test2.bin"
    test_file.write_bytes(b"abc123")
    assert calculate_crc32(test_file) == "cf02bb5c"
