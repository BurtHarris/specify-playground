from pathlib import Path
from unittest.mock import patch, Mock
from src.services.file_scanner import FileScanner

scanner = FileScanner()

user_file1 = Mock(spec=Path)
user_file1.suffix = '.mp4'
user_file1.is_file.return_value = True
user_file1.stat.return_value.st_size = 1024
user_file1.__str__ = lambda: '/test/user_file1.mp4'
user_file1.__fspath__ = lambda: '/test/user_file1.mp4'

user_file2 = Mock(spec=Path)
user_file2.suffix = '.mkv'
user_file2.is_file.return_value = True
user_file2.stat.return_value.st_size = 2048
user_file2.__str__ = lambda: '/test/user_file2.mkv'
user_file2.__fspath__ = lambda: '/test/user_file2.mkv'

non_user_file = Mock(spec=Path)
non_user_file.suffix = '.txt'
non_user_file.is_file.return_value = True
non_user_file.__str__ = lambda: '/test/file.txt'
non_user_file.__fspath__ = lambda: '/test/file.txt'

with patch('pathlib.Path.exists', return_value=True), \
     patch('pathlib.Path.is_dir', return_value=True), \
     patch('os.access', return_value=True), \
     patch('pathlib.Path.iterdir', return_value=[user_file1, user_file2, non_user_file]):
    directory = Path('/test')
    print('Calling scan...')
    res = list(scanner.scan(directory))
    print('Result len:', len(res))
    for f in res:
        print('UserFile:', f, 'size:', f.size)
