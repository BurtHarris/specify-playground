from dependency_injector import providers

from src.lib.container import Container
from src.services.file_scanner import FileScanner


class DummyConfigManager:
    def __init__(self):
        self._store = {}

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value


def test_config_manager_override():
    c = Container()
    dummy = DummyConfigManager()
    c.config_manager.override(providers.Object(dummy))

    cm = c.config_manager()
    cm.set("answer", 42)
    assert cm.get("answer") == 42
    # Subsequent calls return the same overridden instance
    assert c.config_manager() is dummy


def test_database_override(tmp_path):
    # Create a small file to scan
    f = tmp_path / "sample.dat"
    f.write_bytes(b"payload")

    c = Container()

    class StubDB:
        def __init__(self):
            self.calls = 0

        def get_cached_hash(self, path, size, mtime):
            self.calls += 1
            return "stub-hash"

        def set_cached_hash(self, path, size, mtime, hashv):
            self.calls += 1

    stub = StubDB()
    c.database.override(providers.Object(stub))

    db = c.database()
    scanner = FileScanner(db=db)
    scanner.SUPPORTED_EXTENSIONS = None

    results = scanner.scan([tmp_path])
    assert any(r.get("hash") == "stub-hash" for r in results)
    assert stub.calls >= 1
