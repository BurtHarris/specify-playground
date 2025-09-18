"""
Unit tests for VideoFileScanner service.

Tests the VideoFileScanner service including directory scanning,
fi    @patch('os.access')
    @patch('pathlib.Path.exis    @patch('os.access')
    @patch('pathlib.Path.exists')
      @patch('os.access')
       def test_scan_directory_stat_erro    def test_scan_directory_z    def test_scan_directory_mixed_file_types(self, mock_is_file, mock_stat, mock_iterdir, 
                                             mock_is_dir, mock_exists, mock_access, scanner):o_size_files(self, mock_is_file, mock_stat, mock_iterdir, 
                                            mock_is_dir, mock_exists, mock_access, scanner):self, mock_is_file, mock_stat, mock_iterdir, 
                                       mock_is_dir, mock_exists, mock_access, scanner):patch('pathlib    @patch('os.access')
    @patch(    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_mixed_file_types(self, mock_is_file, mock_stat, mock_iterdir, 
                                             mock_is_dir, mock_exists, mock_access, scanner):b.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_zero_size_files(self, mock_is_file, mock_stat, mock_iterdir, 
                                            mock_is_dir, mock_exists, mock_access, scanner):xists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_stat_error(self, mock_is_file, mock_stat, mock_iterdir, 
                                       mock_is_dir, mock_exists, mock_access, scanner):h('pathlib.Path.is_dir')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_non_recursive(self, mock_is_file, mock_stat, mock_glob,
                                          mock_is_dir, mock_exists, mock_access, scanner):  @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_recursive(self, mock_is_file, mock_stat, mock_glob,
                                      mock_rglob, mock_is_dir, mock_exists, mock_access, scanner):ring, and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import os

from src.services.video_file_scanner import VideoFileScanner, DirectoryNotFoundError
from src.models.video_file import VideoFile


class TestVideoFileScanner:
    """Test suite for VideoFileScanner service."""
    
    @pytest.fixture
    def scanner(self):
        """Create a VideoFileScanner instance for testing."""
        return VideoFileScanner()
    
    def test_scanner_creation(self, scanner):
        """Test basic scanner creation."""
        assert isinstance(scanner, VideoFileScanner)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    def test_scan_directory_not_found(self, mock_is_dir, mock_exists, scanner):
        """Test scanning non-existent directory raises error."""
        mock_exists.return_value = False
        mock_is_dir.return_value = False
        
        directory = Path("/nonexistent")
        
        with pytest.raises(DirectoryNotFoundError):
            list(scanner.scan_directory(directory))
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    def test_scan_file_instead_of_directory(self, mock_is_dir, mock_exists, scanner):
        """Test scanning a file instead of directory raises error."""
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        
        directory = Path("/path/to/file.txt")
        
        with pytest.raises(DirectoryNotFoundError):
            list(scanner.scan_directory(directory))
    
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    def test_scan_empty_directory(self, mock_stat, mock_iterdir, mock_is_dir, mock_exists, mock_access, scanner):
        """Test scanning empty directory returns no files."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_access.return_value = True  # Mock directory access permission
        mock_iterdir.return_value = []
        
        directory = Path("/empty")
        result = list(scanner.scan_directory(directory))
        
        assert result == []
    
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_with_video_files(self, mock_is_file, mock_stat, mock_iterdir, 
                                           mock_is_dir, mock_exists, mock_access, scanner):
        """Test scanning directory with video files."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_access.return_value = True
        
        # Create mock files
        video1 = Mock(spec=Path)
        video1.suffix = '.mp4'
        video1.is_file.return_value = True
        video1.stat.return_value.st_size = 1024
        video1.__str__ = lambda: '/test/video1.mp4'
        video1.__fspath__ = lambda: '/test/video1.mp4'
        
        video2 = Mock(spec=Path)
        video2.suffix = '.mkv'
        video2.is_file.return_value = True
        video2.stat.return_value.st_size = 2048
        video2.__str__ = lambda: '/test/video2.mkv'
        video2.__fspath__ = lambda: '/test/video2.mkv'
        
        non_video = Mock(spec=Path)
        non_video.suffix = '.txt'
        non_video.is_file.return_value = True
        non_video.__str__ = lambda: '/test/file.txt'
        non_video.__fspath__ = lambda: '/test/file.txt'
        
        mock_iterdir.return_value = [video1, video2, non_video]
        
        directory = Path("/test")
        result = list(scanner.scan_directory(directory, recursive=False))
        
        assert len(result) == 2
        assert all(isinstance(f, VideoFile) for f in result)
        assert result[0].size == 1024
        assert result[1].size == 2048
    
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_recursive(self, mock_is_file, mock_stat, mock_glob, 
                                    mock_rglob, mock_is_dir, mock_exists, mock_access, scanner):
        """Test recursive directory scanning."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_access.return_value = True
        
        # Create mock video files in subdirectories
        video1 = Mock(spec=Path)
        video1.suffix = '.mp4'
        video1.is_file.return_value = True
        video1.stat.return_value.st_size = 1024
        video1.__str__ = lambda: '/test/subdir/video1.mp4'
        video1.__fspath__ = lambda: '/test/subdir/video1.mp4'
        
        video2 = Mock(spec=Path)
        video2.suffix = '.mov'
        video2.is_file.return_value = True
        video2.stat.return_value.st_size = 3072
        video2.__str__ = lambda: '/test/deeper/video2.mov'
        video2.__fspath__ = lambda: '/test/deeper/video2.mov'
        
        # Mock rglob to return files from recursive search
        mock_rglob.side_effect = lambda pattern: {
            '*.mp4': [video1],
            '*.mkv': [],
            '*.mov': [video2]
        }.get(pattern, [])
        
        directory = Path("/test")
        result = list(scanner.scan_directory(directory, recursive=True))
        
        assert len(result) == 2
        assert result[0].size == 1024
        assert result[1].size == 3072
        
        # Verify rglob was called for each video extension
        assert mock_rglob.call_count == 3
    
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_non_recursive(self, mock_is_file, mock_stat, mock_glob, 
                                        mock_is_dir, mock_exists, mock_access, scanner):
        """Test non-recursive directory scanning."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_access.return_value = True
        
        video1 = Mock(spec=Path)
        video1.suffix = '.mp4'
        video1.is_file.return_value = True
        video1.stat.return_value.st_size = 1024
        video1.__str__ = lambda: '/test/video1.mp4'
        video1.__fspath__ = lambda: '/test/video1.mp4'
        
        # Mock glob to return files from non-recursive search
        mock_glob.side_effect = lambda pattern: {
            '*.mp4': [video1],
            '*.mkv': [],
            '*.mov': []
        }.get(pattern, [])
        
        directory = Path("/test")
        result = list(scanner.scan_directory(directory, recursive=False))
        
        assert len(result) == 1
        assert result[0].size == 1024
        
        # Verify glob was called for each video extension
        assert mock_glob.call_count == 3
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_permission_error(self, mock_is_file, mock_stat, mock_iterdir, 
                                           mock_is_dir, mock_exists, scanner):
        """Test handling permission errors during scanning."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        # Mock permission error
        mock_iterdir.side_effect = PermissionError("Permission denied")
        
        directory = Path("/protected")
        
        with pytest.raises(PermissionError):
            list(scanner.scan_directory(directory))
    
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_stat_error(self, mock_is_file, mock_stat, mock_iterdir, 
                                     mock_is_dir, mock_exists, mock_access, scanner):
        """Test handling stat errors on individual files."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_access.return_value = True
        
        # Create mock files using string paths instead of Mock Path objects
        video1_path = '/test/video1.mp4'
        video2_path = '/test/video2.mkv'
        
        # Mock iterdir to return string paths
        mock_iterdir.return_value = [Path(video1_path), Path(video2_path)]
        
        # Mock is_file to return True for video files
        mock_is_file.side_effect = lambda: True
        
        # Mock stat - video1 succeeds, video2 fails
        def stat_side_effect():
            # Need to track which file is being statted
            # This is a bit tricky with the current mock setup
            # Let's use a different approach
            pass
        
        # Mock Path.stat specifically for our test paths
        original_stat = Path.stat
        def mock_stat_method(self):
            if str(self) == video1_path:
                mock_stat_obj = Mock()
                mock_stat_obj.st_size = 1024
                return mock_stat_obj
            elif str(self) == video2_path:
                raise OSError("Stat failed")
            else:
                return original_stat(self)
        
        with patch.object(Path, 'stat', mock_stat_method):
            directory = Path("/test")
            result = list(scanner.scan_directory(directory, recursive=False))
        
        # Should continue processing despite stat error on one file
        assert len(result) == 1
        assert result[0].size == 1024
    
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_zero_size_files(self, mock_is_file, mock_stat, mock_iterdir, 
                                          mock_is_dir, mock_exists, mock_access, scanner):
        """Test handling of zero-size video files."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_access.return_value = True
        
        # Create mock zero-size video file
        video = Mock(spec=Path)
        video.suffix = '.mp4'
        video.is_file.return_value = True
        video.stat.return_value.st_size = 0
        video.__str__ = lambda: '/test/empty.mp4'
        video.__fspath__ = lambda: '/test/empty.mp4'
        
        mock_iterdir.return_value = [video]
        
        directory = Path("/test")
        result = list(scanner.scan_directory(directory, recursive=False))
        
        # Zero-size files should be skipped
        assert len(result) == 0
    
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.is_file')
    def test_scan_directory_mixed_file_types(self, mock_is_file, mock_stat, mock_iterdir, 
                                           mock_is_dir, mock_exists, mock_access, scanner):
        """Test scanning directory with mixed file types."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_access.return_value = True
        
        # Create various file types
        files = []
        
        # Video files
        for i, ext in enumerate(['.mp4', '.mkv', '.mov', '.MP4'], 1):
            video = Mock(spec=Path)
            video.suffix = ext
            video.is_file.return_value = True
            video.stat.return_value.st_size = 1024 * i
            video.__str__ = lambda ext=ext, i=i: f'/test/video{i}{ext}'
            video.__fspath__ = lambda ext=ext, i=i: f'/test/video{i}{ext}'
            files.append(video)
        
        # Non-video files
        for ext in ['.txt', '.jpg', '.avi', '.wmv']:
            non_video = Mock(spec=Path)
            non_video.suffix = ext
            non_video.is_file.return_value = True
            non_video.__str__ = lambda ext=ext: f'/test/file{ext}'
            non_video.__fspath__ = lambda ext=ext: f'/test/file{ext}'
            files.append(non_video)
        
        # Directory
        subdir = Mock(spec=Path)
        subdir.is_file.return_value = False
        subdir.__str__ = lambda: '/test/subdir'
        subdir.__fspath__ = lambda: '/test/subdir'
        files.append(subdir)
        
        mock_iterdir.return_value = files
        
        directory = Path("/test")
        result = list(scanner.scan_directory(directory, recursive=False))
        
        # Should only return the 4 video files
        assert len(result) == 4
        sizes = [f.size for f in result]
        assert sorted(sizes) == [1024, 2048, 3072, 4096]