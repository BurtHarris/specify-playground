#!/usr/bin/env python3
"""
YAML Export Integration Tests for Video Duplicate Scanner

These tests validate end-to-end YAML export functionality as the primary
export format with human readability focus.

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
import yaml
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import modules for integration testing (will fail until implemented)
try:
    from services.video_file_scanner import VideoFileScanner
    from services.duplicate_detector import DuplicateDetector
    from services.result_exporter import ResultExporter
    from models.scan_result import ScanResult
    from models.scan_metadata import ScanMetadata
    from cli.main import main
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
        def export_yaml(self, result, output_path):
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


class TestYAMLExportIntegration:
    """Test YAML export integration scenarios."""
    
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

    @pytest.mark.integration
    def test_yaml_export_as_default_format(self):
        """Test: YAML export is used as default format."""
        export_file = Path(self.temp_dir) / "results.yaml"
        
        # Integration test: CLI export without specifying format (should default to YAML)
        result = self.cli_runner.invoke(main, [
            "--export", str(export_file),
            str(self.temp_dir)
        ])
        
        # Should succeed and create YAML file
        assert result.exit_code == 0
        assert export_file.exists()
        
        # Should be valid YAML
        with open(export_file, 'r') as f:
            data = yaml.safe_load(f)
            
        assert isinstance(data, dict)
        self.validate_yaml_export_schema(data)

    @pytest.mark.integration
    def test_yaml_human_readable_format(self):
        """Test: YAML export produces human-readable format."""
        export_file = Path(self.temp_dir) / "readable.yaml"
        
        # Integration test: Export with complex data
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        
        scan_result = ScanResult()
        scan_result.duplicate_groups = duplicate_groups
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        scan_result.metadata.total_files_found = len(scanned_files)
        
        self.exporter.export_yaml(scan_result, export_file)
        
        # Validate human readability
        with open(export_file, 'r') as f:
            content = f.read()
            
        # YAML should have readable structure
        assert "version:" in content
        assert "metadata:" in content
        assert "results:" in content
        assert "duplicate_groups:" in content
        
        # Should use proper YAML formatting (indentation, lists, etc.)
        assert "  " in content  # Indentation
        assert "- " in content or content.count("-") > 0  # Lists
        
        # Should be more readable than JSON (no brackets/braces)
        assert content.count("{") == 0  # No JSON-style objects
        assert content.count("[") == 0  # No JSON-style arrays

    @pytest.mark.integration
    def test_yaml_export_file_size_human_readable(self):
        """Test: YAML export shows file sizes in human-readable format."""
        # Create files with known sizes
        sizes_and_names = [
            (1024, "small.mp4"),           # 1 KB
            (1048576, "medium.mkv"),       # 1 MB  
            (1073741824, "large.mov")      # 1 GB
        ]
        
        for size, name in sizes_and_names:
            file_path = Path(self.temp_dir) / name
            content = b"X" * size
            with open(file_path, 'wb') as f:
                f.write(content)
        
        export_file = Path(self.temp_dir) / "file_sizes.yaml"
        
        # Integration test: Export with file size information
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        scan_result = ScanResult()
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        scan_result.metadata.total_files_found = len(scanned_files)
        
        self.exporter.export_yaml(scan_result, export_file)
        
        # Validate human-readable file sizes
        with open(export_file, 'r') as f:
            content = f.read()
            
        # Should contain human-readable size units
        size_units = ["B", "KB", "MB", "GB"]
        assert any(unit in content for unit in size_units), "Should contain human-readable size units"
        
        # Should not show raw byte counts for large files
        assert "1073741824" not in content  # Raw 1GB byte count should be formatted

    @pytest.mark.integration 
    def test_yaml_export_preserves_unicode(self):
        """Test: YAML export correctly preserves Unicode characters."""
        # Create files with Unicode names
        unicode_files = [
            "电影.mp4",           # Chinese
            "фильм.mkv",         # Cyrillic  
            "película.mov",      # Spanish
            "movie_🎬.mp4"      # Emoji
        ]
        
        content = b"Unicode test content" * 1000
        for filename in unicode_files:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        export_file = Path(self.temp_dir) / "unicode.yaml"
        
        # Integration test: Scan and export Unicode filenames
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        scan_result = ScanResult()
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        scan_result.metadata.total_files_found = len(scanned_files)
        
        self.exporter.export_yaml(scan_result, export_file)
        
        # Validate Unicode preservation  
        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # All Unicode characters should be preserved
        for filename in unicode_files:
            assert filename in content, f"Unicode filename {filename} should be preserved"

    @pytest.mark.integration
    def test_yaml_export_readable_timestamps(self):
        """Test: YAML export uses readable timestamp format."""
        export_file = Path(self.temp_dir) / "timestamps.yaml"
        
        # Integration test: Export with specific timestamp
        scan_result = ScanResult()
        scan_result.metadata.scan_date = "2025-09-17T15:30:45.123Z"
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        
        self.exporter.export_yaml(scan_result, export_file)
        
        # Validate timestamp readability
        with open(export_file, 'r') as f:
            content = f.read()
            
        # Should contain the timestamp in readable format
        assert "2025-09-17T15:30:45.123Z" in content
        
        # Should be on its own line with clear labeling
        assert "scan_date:" in content

    @pytest.mark.integration
    def test_yaml_export_structured_duplicate_groups(self):
        """Test: YAML export shows duplicate groups in structured, readable format."""
        export_file = Path(self.temp_dir) / "duplicates.yaml"
        
        # Integration test: Export with duplicate groups
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        
        scan_result = ScanResult()
        scan_result.duplicate_groups = duplicate_groups
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        
        self.exporter.export_yaml(scan_result, export_file)
        
        # Validate duplicate group structure
        with open(export_file, 'r') as f:
            content = f.read()
            data = yaml.safe_load(f)
            f.seek(0)
            content = f.read()
            
        # Should have clear duplicate group structure
        assert "duplicate_groups:" in content
        
        # Should use YAML list formatting
        if duplicate_groups:
            assert "- files:" in content or "files:" in content
            
        # Should include file information in readable format
        if duplicate_groups and len(duplicate_groups[0].files) > 0:
            # Should mention file paths
            file_names = [f.path.name for f in duplicate_groups[0].files]
            for name in file_names:
                assert name in content

    @pytest.mark.integration
    def test_yaml_export_comments_and_documentation(self):
        """Test: YAML export includes helpful comments and documentation."""
        export_file = Path(self.temp_dir) / "documented.yaml"
        
        # Integration test: Export with full documentation
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        potential_matches = self.detector.find_potential_matches(scanned_files)
        
        scan_result = ScanResult()
        scan_result.duplicate_groups = duplicate_groups
        scan_result.potential_matches = potential_matches
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        
        self.exporter.export_yaml(scan_result, export_file)
        
        # Validate documentation/comments
        with open(export_file, 'r') as f:
            content = f.read()
            
        # Should include helpful comments (YAML comments start with #)
        comment_indicators = ["#", "# ", "# Video Duplicate Scanner", "# Results"]
        has_comments = any(indicator in content for indicator in comment_indicators)
        
        # If no comments, should at least have clear section headers
        if not has_comments:
            assert "metadata:" in content
            assert "results:" in content
            assert "duplicate_groups:" in content

    @pytest.mark.integration
    def test_yaml_export_potential_savings_calculation(self):
        """Test: YAML export includes potential space savings in readable format."""
        export_file = Path(self.temp_dir) / "savings.yaml"
        
        # Integration test: Export with savings calculation
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        
        scan_result = ScanResult()
        scan_result.duplicate_groups = duplicate_groups
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        
        # Calculate potential savings
        total_savings = 0
        for group in duplicate_groups:
            if len(group.files) > 1:
                # Savings = (number of duplicates - 1) * file size
                file_size = group.files[0].size if hasattr(group.files[0], 'size') else 0
                total_savings += (len(group.files) - 1) * file_size
        
        scan_result.statistics = {"potential_savings_bytes": total_savings}
        
        self.exporter.export_yaml(scan_result, export_file)
        
        # Validate savings information
        with open(export_file, 'r') as f:
            content = f.read()
            
        # Should include savings information
        savings_keywords = ["savings", "potential", "space", "duplicate"]
        has_savings_info = any(keyword in content.lower() for keyword in savings_keywords)
        assert has_savings_info, "Should include potential savings information"

    @pytest.mark.integration
    def test_yaml_export_error_reporting(self):
        """Test: YAML export includes error information in readable format."""
        # Create a protected file to generate errors
        protected_file = Path(self.temp_dir) / "protected.mp4"
        protected_file.touch()
        protected_file.chmod(0o000)
        
        export_file = Path(self.temp_dir) / "errors.yaml"
        
        try:
            # Integration test: Export with errors
            scan_result = ScanResult()
            scan_result.metadata.scanned_directory = str(self.temp_dir)
            scan_result.metadata.errors = [
                f"Permission denied: {protected_file}",
                "Could not read file: insufficient permissions"
            ]
            
            self.exporter.export_yaml(scan_result, export_file)
            
            # Validate error reporting
            with open(export_file, 'r') as f:
                content = f.read()
                
            # Should include error section
            assert "errors:" in content
            assert "Permission denied" in content
            
            # Should be in readable list format
            assert "- " in content  # YAML list format
            
        finally:
            # Restore permissions for cleanup
            protected_file.chmod(0o644)

    @pytest.mark.integration
    def test_yaml_vs_json_size_comparison(self):
        """Test: YAML export is more compact than equivalent JSON for readability."""
        yaml_file = Path(self.temp_dir) / "results.yaml"
        json_file = Path(self.temp_dir) / "results.json"
        
        # Integration test: Export same data in both formats
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        
        scan_result = ScanResult()
        scan_result.duplicate_groups = duplicate_groups
        scan_result.metadata.scanned_directory = str(self.temp_dir)
        
        # Export to both formats
        self.exporter.export_yaml(scan_result, yaml_file)
        self.exporter.export_json(scan_result, json_file)
        
        # Compare readability characteristics
        with open(yaml_file, 'r') as f:
            yaml_content = f.read()
            
        with open(json_file, 'r') as f:
            json_content = f.read()
            
        # YAML should have fewer special characters (more readable)
        yaml_special_chars = yaml_content.count('{') + yaml_content.count('}') + yaml_content.count('"')
        json_special_chars = json_content.count('{') + json_content.count('}') + json_content.count('"')
        
        # YAML should have significantly fewer special characters
        assert yaml_special_chars < json_special_chars * 0.5, "YAML should be more readable than JSON"

    @pytest.mark.integration
    def test_yaml_export_automatic_extension_detection(self):
        """Test: Export automatically detects YAML format from .yaml extension."""
        yaml_file = Path(self.temp_dir) / "auto_detect.yaml"
        
        # Integration test: Export should automatically use YAML format
        result = self.cli_runner.invoke(main, [
            "--export", str(yaml_file),
            str(self.temp_dir)
        ])
        
        assert result.exit_code == 0
        assert yaml_file.exists()
        
        # Should be valid YAML (not JSON)
        with open(yaml_file, 'r') as f:
            content = f.read()
            
        # Should not contain JSON-style syntax
        assert content.count('{') == 0
        assert content.count('[') == 0
        
        # Should contain YAML-style syntax
        assert ':' in content
        assert content.count('- ') > 0 or 'files:' in content

    def validate_yaml_export_schema(self, data):
        """Validate that YAML export data conforms to expected schema."""
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