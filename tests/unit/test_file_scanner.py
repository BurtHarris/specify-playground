from src.services.file_scanner import FileScanner
from src.services.file_database import InMemoryFileDatabase


def test_file_scanner_hashes_and_caches(tmp_path, monkeypatch):
    # create two files
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"hello world")
    b.write_bytes(b"another file")

    # force scanner to use an in-memory DB instance
    monkeypatch.setattr(
        "src.services.file_scanner.get_database",
        lambda db_path=None: InMemoryFileDatabase(),
    )

    scanner = FileScanner(db_path=None, patterns=["*.txt"], recursive=False)
    results = scanner.scan([tmp_path])

    paths = {r["path"]: r for r in results}
    assert str(a) in paths
    assert str(b) in paths
    assert paths[str(a)]["hash"] is not None
    assert paths[str(b)]["hash"] is not None


from types import SimpleNamespace


def test_validate_file_nonexistent(tmp_path):
    scanner = FileScanner()
    missing = tmp_path / "nope.mp4"
    assert not scanner.validate_file(missing)


def test_validate_file_zero_size(tmp_path):
    scanner = FileScanner()
    f = tmp_path / "empty.mp4"
    f.write_bytes(b"")
    assert f.stat().st_size == 0
    assert not scanner.validate_file(f)


def test_validate_file_positive_size(tmp_path):
    scanner = FileScanner()
    f = tmp_path / "video.mp4"
    f.write_bytes(b"\x00\x01\x02")
    assert f.stat().st_size > 0
    assert scanner.validate_file(f)


def test_should_include_file_cloud_filters():
    scanner = FileScanner()
    # Simple stand-in for UserFile with required attributes
    local = SimpleNamespace(is_local=True, is_cloud_only=False)
    cloud = SimpleNamespace(is_local=False, is_cloud_only=True)

    # 'all' includes both
    assert scanner._should_include_file(local, "all")
    assert scanner._should_include_file(cloud, "all")

    # 'local' only includes local files
    assert scanner._should_include_file(local, "local")
    assert not scanner._should_include_file(cloud, "local")

    # 'cloud-only' only includes cloud-only
    assert not scanner._should_include_file(local, "cloud-only")
    assert scanner._should_include_file(cloud, "cloud-only")
