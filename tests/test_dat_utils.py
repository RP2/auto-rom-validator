import glob
from pathlib import Path

import pytest

from utils.dat_utils import parse_custom_dat, parse_dat

# Find all possible No-Intro XML DATs for NDS Encrypted
no_intro_nds_encrypted_dats = glob.glob(
    "dats/Nintendo - Nintendo DS (Encrypted) (*.dat"
)


@pytest.mark.parametrize(
    "dat_path,expected_sha1,expected_md5,expected_crc,expected_filename",
    [
        *[
            (
                Path(dat),
                "e2fd3a208153d2096cfddcc82bb14f34a5917067",  # 007 - Blood Stone (USA)
                "03c516c5c6d736b935d1626ad297e3aa",
                "021595f7",
                "007 - Blood Stone (USA).nds",
            )
            for dat in no_intro_nds_encrypted_dats
        ],
        *[
            (
                Path(dat),
                # 007 - Quantum of Solace (USA) (En,Fr)
                "d2a7729c02f5b409ea5032e0a1dd6416816eeb10",
                "23d8012fa0374a06214072156eb4fc28",
                "67f2b05f",
                "007 - Quantum of Solace (USA) (En,Fr).nds",
            )
            for dat in no_intro_nds_encrypted_dats
        ],
        *[
            (
                Path(dat),
                # Learn with Pokemon - Typing Adventure (Europe)
                "e4d14529bf26eb8af1763a399ee6e7b176b87840",
                "8c39b2846857f4ca276a2a167964e1dd",
                "28dd5577",
                "Learn with Pokemon - Typing Adventure (Europe).nds",
            )
            for dat in no_intro_nds_encrypted_dats
        ],
    ],
)
def test_parse_dat_no_intro_xml(
    dat_path, expected_sha1, expected_md5, expected_crc, expected_filename
):
    sha1_map, md5_map, crc32_map = parse_custom_dat(dat_path)
    assert expected_sha1 in sha1_map
    assert expected_md5 in md5_map
    assert expected_crc in crc32_map
    assert expected_filename in sha1_map[expected_sha1]
    assert expected_filename in md5_map[expected_md5]
    assert expected_filename in crc32_map[expected_crc]


# Test with real clrmamepro DAT (text format)


@pytest.mark.parametrize(
    "dat_path,expected_sha1,expected_md5,expected_crc,expected_filename",
    [
        (
            Path("dats/Nintendo DS.dat"),
            "dadbccf3ccaa2a084d4fe3ece410c495c842811f",
            "03ba799635f3e34cfd64f353330f6799",
            "8aa9e6c7",
            "007 - Blood Stone (USA).nds",
        ),
        (
            Path("dats/Nintendo DS.dat"),
            "c2d2434d0323312f4fc2680d8ff9659be7e38201",
            "ed77d9951a61e1b2aebbdc3c3edd7f07",
            "283013fa",
            "007 - Quantum of Solace (USA) (En,Fr).nds",
        ),
    ],
)
def test_parse_dat_clrmamepro(
    dat_path, expected_sha1, expected_md5, expected_crc, expected_filename
):
    sha1_map, md5_map, crc32_map = parse_dat(dat_path)
    assert expected_sha1 in sha1_map
    assert expected_md5 in md5_map
    assert expected_crc in crc32_map
    assert expected_filename in sha1_map[expected_sha1]
    assert expected_filename in md5_map[expected_md5]
    assert expected_filename in crc32_map[expected_crc]
