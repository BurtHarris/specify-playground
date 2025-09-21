import hashlib

import pytest

from src.models.file import UserFile
from src.models.duplicate_group import DuplicateGroup


def test_userfile_size_and_hash(tmp_path):
    data = b"hello world"
    f = tmp_path / "hello.txt"
    f.write_bytes(data)

    uf = UserFile(f)

    # size property reads from filesystem
    assert uf.size == len(data)

    # compute_hash should return blake2b of the contents
    expected = hashlib.blake2b(data).hexdigest()
    assert uf.compute_hash() == expected

    d = uf.to_dict()
    assert d["path"] == str(f)
    assert d["size"] == len(data)
    assert d["hash"] == expected


def test_duplicate_group_basic(tmp_path):
    content = b"same-content"
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    f1.write_bytes(content)
    f2.write_bytes(content)

    uf1 = UserFile(f1)
    uf2 = UserFile(f2)

    h = uf1.compute_hash()
    # Initialize group with two identical files
    group = DuplicateGroup(h, [uf1, uf2])

    assert group.is_duplicate_group
    assert group.file_count == 2
    assert set(str(p) for p in group.paths) == {str(f1), str(f2)}

    # Adding a file with different hash should raise
    f3 = tmp_path / "c.bin"
    f3.write_bytes(b"different")
    uf3 = UserFile(f3)
    with pytest.raises(ValueError):
        group.add_file(uf3)

    # merge_group should accept same-hash group
    other = DuplicateGroup(h, [uf1])
    group.merge_group(other)
    assert group.file_count >= 2
