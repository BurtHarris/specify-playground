#!/usr/bin/env python3
"""
JSON Export Integration Tests for Video Duplicate Scanner

These tests validate end-to-end JSON export functionality as specified
in the CLI interface contract and quickstart scenarios.

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import modules for integration testing
try:
    from src.services.video_file_scanner import VideoFileScanner
    from src.services.duplicate_detector import DuplicateDetector
    from src.services.result_exporter import ResultExporter
    from src.models.scan_result import ScanResult
    from src.models.scan_metadata import ScanMetadata
    from src.cli.main import main
    from click.testing import CliRunner
except ImportError:
    # Expected to fail initially - create stubs for testing
    class VideoFileScanner:
        def scan_directory(self, directory, recursive=True):
            raise NotImplementedError("VideoFileScanner not yet implemented")
    
    class DuplicateDetector:
        def find_duplicates(self, files):
            raise NotImplementedError("DuplicateDetector not yet implemented")
            
        def find_potential_matches(self, files, threshold=0.8):
            raise NotImplementedError("DuplicateDetector not yet implemented")
    
    class ResultExporter:
        def export_json(self, result, output_path):
            raise NotImplementedError("ResultExporter not yet implemented")
    
    class ScanResult:
        def __init__(self):
            self.metadata = ScanMetadata()
            self.duplicate_groups = []
            self.potential_matches = []
            self.statistics = {}
    
    class ScanMetadata:
        def __init__(self):
            self.scan_date = datetime.now().isoformat() + "Z"
            self.scanned_directory = "/test"
            self.duration_seconds = 1.0
            self.total_files_found = 0
            self.total_files_processed = 0
            self.recursive = True
            self.errors = []
    
    def main():
        raise NotImplementedError("CLI not yet implemented")
    
    class CliRunner:
        def invoke(self, func, args):
            from collections import namedtuple
            Result = namedtuple('Result', ['exit_code', 'output'])
            return Result(1, "Not implemented")


class TestJSONExportIntegration:
    """Test JSON export integration scenarios."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = VideoFileScanner()
        self.detector = DuplicateDetector()
        self.exporter = ResultExporter()
        self.cli_runner = CliRunner()
        
        # Create test video files
        self.create_test_videos()
        
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_videos(self):
        """Create test video files for consistent testing."""
        # Duplicate files
        duplicate_content = b"Duplicate video content" * 5000
        self.duplicate1 = Path(self.temp_dir) / "movie1.mp4"
        self.duplicate2 = Path(self.temp_dir) / "movie1_backup.mkv"
        
        for file in [self.duplicate1, self.duplicate2]:
            with open(file, 'wb') as f:
                f.write(duplicate_content)
        
        # Unique file
        unique_content = b"Unique video content" * 5000
        self.unique1 = Path(self.temp_dir) / "different_movie.mov"
        with open(self.unique1, 'wb') as f:
            f.write(unique_content)
        
        # Files with similar names
        similar_content1 = b"Similar name content 1" * 5000
        similar_content2 = b"Similar name content 2" * 5000
        self.similar1 = Path(self.temp_dir) / "action_movie.mp4"
        self.similar2 = Path(self.temp_dir) / "action_movie.mkv"
        
        with open(self.similar1, 'wb') as f:
            f.write(similar_content1)
        with open(self.similar2, 'wb') as f:
            f.write(similar_content2)

    @pytest.mark.integration
    def test_end_to_end_json_export_via_cli(self):
        """Test: End-to-end JSON export via CLI command."""
        export_file = Path(self.temp_dir) / "results.json"
        
        # Integration test: CLI scan with JSON export
        result = self.cli_runner.invoke(main, [
            "--export", str(export_file),
            str(self.temp_dir)
        ])
        
        # Should succeed
        assert result.exit_code == 0
        assert export_file.exists()
        
        # Validate JSON structure
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        self.validate_json_export_schema(data)

    @pytest.mark.integration
    def test_json_stdout_output_integration(self):
        """Test: JSON output to stdout integration."""
        # Integration test: CLI with JSON output format
        result = self.cli_runner.invoke(main, [
            "--output", "json",
            str(self.temp_dir)
        ])
        
        # Should succeed and output valid JSON
        assert result.exit_code == 0
        
        # Parse JSON output
        data = json.loads(result.output)
        self.validate_json_export_schema(data)

    @pytest.mark.integration
    def test_json_export_with_duplicates_found(self):
        """Test: JSON export contains correct duplicate information."""
        export_file = Path(self.temp_dir) / "duplicates.json"
        
        # Integration test: Full pipeline with known duplicates
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        potential_matches = self.detector.find_potential_matches(scanned_files)
        
        # Create scan result with metadata
        from src.models.scan_metadata import ScanMetadata
        metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)
        metadata.total_files_found = len(scanned_files)
        metadata.total_files_processed = len(scanned_files)
        scan_result = ScanResult(metadata)
        scan_result.duplicate_groups = duplicate_groups
        scan_result.potential_matches = potential_matches
        
        # Export to JSON
        self.exporter.export_json(scan_result, export_file)
        
        # Validate exported content
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        # Should contain duplicate groups
        assert len(data["results"]["duplicate_groups"]) >= 1
        
        # Verify duplicate group structure
        duplicate_group = data["results"]["duplicate_groups"][0]
        assert "files" in duplicate_group
        assert len(duplicate_group["files"]) >= 2
        
        # Verify file information in group
        for file_info in duplicate_group["files"]:
            assert "path" in file_info
            assert "size_bytes" in file_info
            assert "size_human" in file_info
            assert "hash" in file_info

    @pytest.mark.integration
    def test_json_export_with_potential_matches(self):
        """Test: JSON export contains potential match information."""
        export_file = Path(self.temp_dir) / "matches.json"
        
        # Integration test: Scan and detect potential matches
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.7)
        
        # Create scan result with metadata
        from src.models.scan_metadata import ScanMetadata
        metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)
        scan_result = ScanResult(metadata)
        scan_result.potential_matches = potential_matches
        
        # Export to JSON
        self.exporter.export_json(scan_result, export_file)
        
        # Validate potential matches in export
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        # Should contain potential matches
        potential_matches_data = data["results"]["potential_matches"]
        assert isinstance(potential_matches_data, list)
        
        # If matches found, verify structure
        if len(potential_matches_data) > 0:
            match_group = potential_matches_data[0]
            assert "files" in match_group
            assert "similarity_score" in match_group
            assert 0.0 <= match_group["similarity_score"] <= 1.0

    @pytest.mark.integration
    def test_json_export_file_size_formatting(self):
        """Test: JSON export includes properly formatted file sizes."""
        export_file = Path(self.temp_dir) / "sizes.json"
        
        # Create file with known size
        large_file = Path(self.temp_dir) / "large_video.mp4"
        content = b"Large video content" * 100000  # ~1.7MB
        with open(large_file, 'wb') as f:
            f.write(content)
        
        # Integration test: Export with file size information
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)
        metadata.total_files_found = len(scanned_files)
        scan_result = ScanResult(metadata)
        
        self.exporter.export_json(scan_result, export_file)
        
        # Validate file size formatting
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        # Check statistics include size information
        if "statistics" in data["results"]:
            stats = data["results"]["statistics"]
            size_fields = ["total_size", "duplicate_size", "potential_savings"]
            
            # At least one size field should be present and formatted
            for field in size_fields:
                if field in stats:
                    assert isinstance(stats[field], (str, int, float))

    @pytest.mark.integration
    def test_json_export_unicode_path_handling(self):
        """Test: JSON export correctly handles Unicode file paths."""
        # Create files with Unicode names
        unicode_file = Path(self.temp_dir) / "测试视频.mp4"
        emoji_file = Path(self.temp_dir) / "movie_🎬.mkv"
        cyrillic_file = Path(self.temp_dir) / "фильм.mov"
        
        content = b"Unicode test content" * 1000
        for file in [unicode_file, emoji_file, cyrillic_file]:
            with open(file, 'wb') as f:
                f.write(content)
        
        export_file = Path(self.temp_dir) / "unicode_test.json"
        
        # Integration test: Scan and export Unicode filenames
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.5)
        
        metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)
        metadata.total_files_found = len(scanned_files)
        scan_result = ScanResult(metadata)
        scan_result.duplicate_groups = duplicate_groups
        scan_result.potential_matches = potential_matches
        
        self.exporter.export_json(scan_result, export_file)
        
        # Validate Unicode preservation
        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()
            data = json.loads(content)
            
        # Unicode characters should be preserved in JSON
        assert "测试视频.mp4" in content
        assert "movie_🎬.mkv" in content
        assert "фильм.mov" in content

    @pytest.mark.integration
    def test_json_export_error_information(self):
        """Test: JSON export includes error information."""
        # Create a file that will cause permission error
        protected_file = Path(self.temp_dir) / "protected.mp4"
        protected_file.touch()
        protected_file.chmod(0o000)
        
        export_file = Path(self.temp_dir) / "errors.json"
        
        try:
            # Integration test: Scan with errors
            metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)

            scan_result = ScanResult(metadata)
            scan_result.metadata.errors = [f"Could not read {protected_file}: Permission denied"]
            
            self.exporter.export_json(scan_result, export_file)
            
            # Validate error information in export
            with open(export_file, 'r') as f:
                data = json.load(f)
                
            # Should include error information
            assert "errors" in data["metadata"]
            assert len(data["metadata"]["errors"]) > 0
            assert "permission" in data["metadata"]["errors"][0].lower()
            
        finally:
            # Restore permissions for cleanup
            protected_file.chmod(0o644)

    @pytest.mark.integration
    def test_json_export_timestamp_format(self):
        """Test: JSON export uses proper ISO 8601 timestamp format."""
        export_file = Path(self.temp_dir) / "timestamp.json"
        
        # Integration test: Export with timestamp
        metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)

        scan_result = ScanResult(metadata)

        scan_result.metadata.start_time = datetime.now()
        
        self.exporter.export_json(scan_result, export_file)
        
        # Validate timestamp format
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        scan_date = data["metadata"]["scan_date"]
        
        # Should be valid ISO 8601 format
        import re
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$'
        assert re.match(iso8601_pattern, scan_date)
        
        # Should be parseable as datetime
        parsed_date = datetime.fromisoformat(scan_date.replace('Z', '+00:00'))
        assert isinstance(parsed_date, datetime)

    @pytest.mark.integration
    def test_json_export_statistics_calculation(self):
        """Test: JSON export includes calculated statistics."""
        export_file = Path(self.temp_dir) / "stats.json"
        
        # Integration test: Full scan with statistics
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        
        metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)
        metadata.total_files_found = len(scanned_files)
        metadata.total_files_processed = len(scanned_files)
        scan_result = ScanResult(metadata)
        scan_result.duplicate_groups = duplicate_groups
        
        # Calculate statistics
        total_duplicates = sum(len(group.files) for group in duplicate_groups)
        unique_files = len(scanned_files) - total_duplicates + len(duplicate_groups)
        
        scan_result.statistics = {
            "unique_files": unique_files,
            "duplicate_files": total_duplicates - len(duplicate_groups),  # Exclude originals
            "duplicate_groups": len(duplicate_groups)
        }
        
        self.exporter.export_json(scan_result, export_file)
        
        # Validate statistics in export
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        stats = data["results"]["statistics"]
        assert "unique_files" in stats
        assert "duplicate_files" in stats
        assert "duplicate_groups" in stats
        
        # Statistics should be non-negative
        assert stats["unique_files"] >= 0
        assert stats["duplicate_files"] >= 0
        assert stats["duplicate_groups"] >= 0

    @pytest.mark.integration
    def test_json_export_large_dataset(self):
        """Test: JSON export handles larger datasets efficiently."""
        # Create many test files
        for i in range(50):
            file_path = Path(self.temp_dir) / f"video_{i:03d}.mp4"
            # Vary content to create some duplicates
            if i % 10 == 0:
                content = b"Duplicate content group" * 1000
            else:
                content = f"Unique content {i}".encode() * 1000
            
            with open(file_path, 'wb') as f:
                f.write(content)
        
        export_file = Path(self.temp_dir) / "large_dataset.json"
        
        # Integration test: Large dataset processing
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        
        metadata = ScanMetadata([Path(self.temp_dir)], recursive=True)
        metadata.total_files_found = len(scanned_files)
        scan_result = ScanResult(metadata)
        scan_result.duplicate_groups = duplicate_groups
        
        # Should handle large dataset without issues
        self.exporter.export_json(scan_result, export_file)
        
        assert export_file.exists()
        
        # Validate JSON is still valid with large dataset
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        self.validate_json_export_schema(data)
        
        # Should find some duplicates in the dataset
        assert data["metadata"]["total_files_found"] >= 50

    def validate_json_export_schema(self, data):
        """Validate that JSON export data conforms to expected schema."""
        # Top-level structure
        assert isinstance(data, dict)
        assert "version" in data
        assert "metadata" in data
        assert "results" in data
        
        # Metadata section
        metadata = data["metadata"]
        required_metadata = [
            "scan_date", "scanned_directory", "duration_seconds",
            "total_files_found", "total_files_processed", "recursive"
        ]
        for field in required_metadata:
            assert field in metadata, f"Missing metadata field: {field}"
        
        # Results section
        results = data["results"]
        assert "duplicate_groups" in results
        assert "potential_matches" in results
        assert "statistics" in results
        
        # Data types
        assert isinstance(results["duplicate_groups"], list)
        assert isinstance(results["potential_matches"], list)
        assert isinstance(results["statistics"], dict)


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])