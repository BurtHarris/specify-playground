import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Ensure workspace root is importable when running this script directly
import pathlib as _pl

sys.path.insert(0, str(_pl.Path(r"e:/specify-playground").resolve()))
import os

# Enable debug tracing in file_scanner for this run
os.environ["SPECIFY_DEBUG_VALIDATE"] = "1"

from src.services.file_scanner import FileScanner

scanner = FileScanner()

# Create mock files similar to tests
user_file1 = Mock(spec=Path)
user_file1.suffix = ".mp4"
user_file1.is_file.return_value = True
mock_stat_obj = Mock()
mock_stat_obj.st_size = 1024
user_file1.stat.return_value = mock_stat_obj
user_file1.__str__ = lambda: "/test/user_file1.mp4"
user_file1.__fspath__ = lambda: "/test/user_file1.mp4"

print("is_mock attribute present:", hasattr(user_file1, "_mock_name"))
print("has __fspath__:", hasattr(user_file1, "__fspath__"))
print("suffix:", getattr(user_file1, "suffix", None))

try:
    valid = scanner.validate_file(user_file1)
    print("validate_file returned:", valid)
except Exception as e:
    import traceback

    print("validate_file raised:", e)
    traceback.print_exc()

# Also test with MagicMock variant
user_file2 = MagicMock(spec=Path)
user_file2.suffix = ".mkv"
user_file2.is_file.return_value = True
user_file2.stat.return_value.st_size = 2048
user_file2.__str__.return_value = "/test/user_file2.mkv"
user_file2.__fspath__.return_value = "/test/user_file2.mkv"

print("\nMagicMock test:")
print("is_mock:", hasattr(user_file2, "_mock_name"))
print("suffix:", getattr(user_file2, "suffix", None))
try:
    print("validate_file MagicMock ->", scanner.validate_file(user_file2))
except Exception as e:
    print("raised:", e)

# Test direct Path to show baseline
p = Path("/test/file.mp4")
print("\nReal Path validate ->", scanner._is_video_file(p))

print("\nDone")

# Now simulate a directory mock with iterdir returning the user_file mocks
print("\nSimulate directory iterdir behavior:")
dir_mock = Mock(spec=Path)
dir_mock.exists.return_value = True
dir_mock.is_dir.return_value = True
dir_mock.iterdir.return_value = [user_file1, user_file2]
dir_mock.glob.side_effect = lambda pattern: []
dir_mock.__str__ = lambda: "/test"
dir_mock.__fspath__ = lambda: "/test"

print("Calling scanner.scan on directory mock...")
res = list(scanner.scan(dir_mock))
print("scan returned", res)
for f in res:
    try:
        print("-> UserFile size:", f.size)
    except Exception as e:
        print("-> size access error:", e)
