from pathlib import Path
from unittest.mock import Mock, patch
from src.services.file_scanner import FileScanner

scanner = FileScanner()

# Set up mocks matching the test
user_file1 = Mock(spec=Path)
user_file1.suffix = ".mp4"
user_file1.is_file.return_value = True
user_file1.stat.return_value.st_size = 1024
user_file1.__str__ = lambda: "/test/user_file1.mp4"
user_file1.__fspath__ = lambda: "/test/user_file1.mp4"

user_file2 = Mock(spec=Path)
user_file2.suffix = ".mkv"
user_file2.is_file.return_value = True
user_file2.stat.return_value.st_size = 2048
user_file2.__str__ = lambda: "/test/user_file2.mkv"
user_file2.__fspath__ = lambda: "/test/user_file2.mkv"

non_user_file = Mock(spec=Path)
non_user_file.suffix = ".txt"
non_user_file.is_file.return_value = True
non_user_file.__str__ = lambda: "/test/file.txt"
non_user_file.__fspath__ = lambda: "/test/file.txt"

mock_iter = [user_file1, user_file2, non_user_file]

# Patch Path.exists/is_dir/iterdir/os.access during this run
with patch("pathlib.Path.exists", return_value=True), patch(
    "pathlib.Path.is_dir", return_value=True
), patch("pathlib.Path.iterdir", return_value=mock_iter), patch(
    "os.access", return_value=True
):
    entries = list(Path("/test").iterdir())
    print("Entries returned by iterdir():", entries)
    for e in entries:
        try:
            print(
                "Entry is_file():",
                e.is_file(),
                "suffix:",
                getattr(e, "suffix", None),
                "is_video_ext:",
                getattr(e, "suffix", "").lower() in {".mp4", ".mkv", ".mov"},
            )
        except Exception as ex:
            print("Entry inspect error:", ex)
    # Direct validations
    for e in entries:
        try:
            print(
                "Direct validate_file call for",
                e,
                "->",
                scanner.validate_file(e),
            )
        except Exception as ex:
            print("validate_file raised:", ex)
    result = list(scanner.scan_directory(Path("/test"), recursive=False))
    print("Result length:", len(result))
    for f in result:
        try:
            print("File:", f, "size:", f.size)
        except Exception as e:
            print("File object error:", e)

print("Done")
