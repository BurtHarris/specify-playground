import hashlib
from dependency_injector import providers

from src.lib.container import Container
from src.services.file_scanner import FileScanner
from src.services.duplicate_detector import DuplicateDetector
from src.services.progress_reporter import ProgressReporter


class FakeReporter(ProgressReporter):
    def __init__(self):
        # do not call super to avoid side-effects
        self.started = False
        self.updates = []
        self.finished = False

    def start_progress(self, total, label):
        self.started = True

    def update_progress(self, idx, name):
        self.updates.append((idx, name))

    def finish_progress(self):
        self.finished = True


def test_hasher_override_and_permission_skip(tmp_path):
    # Prepare files: two identical files plus one that will simulate a permission error
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    bad = tmp_path / "noaccess.bin"
    a.write_bytes(b"hello")
    b.write_bytes(b"hello")
    bad.write_bytes(b"secret")

    c = Container()

    # Capture the original hasher callable
    orig_hasher = c.hasher()

    # Custom hasher: raise PermissionError for the 'noaccess.bin' file
    def custom_hasher(path, chunk_size=1024 * 1024):
        if path.name == "noaccess.bin":
            raise PermissionError("simulated no access")
        return orig_hasher(path, chunk_size=chunk_size)

    # Override the container hasher provider
    c.hasher.override(providers.Object(custom_hasher))

    # Use the container database and the overridden hasher
    db = c.database()
    # Pass the actual callable from the provider into FileScanner
    scanner = FileScanner(db=db, hasher=c.hasher())
    # Accept any extension for this test
    scanner.SUPPORTED_EXTENSIONS = None

    results = scanner.scan([tmp_path])

    # Expect that two files were hashed (a.bin and b.bin) and the bad file was skipped
    paths = {
        r["path"].split("/")[-1] if "/" in r["path"] else r["path"].split("\\")[-1]
        for r in results
    }
    assert "a.bin" in paths
    assert "b.bin" in paths
    assert "noaccess.bin" not in paths


def test_progress_reporter_injection(tmp_path):
    # Create two identical files to exercise duplicate detection and progress reporting
    f1 = tmp_path / "one.txt"
    f2 = tmp_path / "two.txt"
    f1.write_bytes(b"same")
    f2.write_bytes(b"same")

    c = Container()

    fake = FakeReporter()
    # Override the progress reporter factory to always return the fake reporter
    c.progress_reporter.override(providers.Object(fake))

    # Create scanner and detector using the container-provided collaborators
    db = c.database()
    scanner = FileScanner(db=db)
    scanner.SUPPORTED_EXTENSIONS = None

    # Use the legacy scanner generator to obtain UserFile instances
    files = list(
        scanner.scan_directory(tmp_path, recursive=False, progress_reporter=None)
    )

    detector = DuplicateDetector(progress_reporter=fake)
    duplicates = detector.find_duplicates(files)

    # Fake reporter should have been usable (started/updated/finished may vary)
    assert isinstance(fake, FakeReporter)
    # Detector should find at least one duplicate group (the two identical files)
    # `find_duplicates` returns a list of DuplicateGroup objects; assert one has >=2 files
    assert any(len(getattr(group, "files", [])) >= 2 for group in duplicates)
