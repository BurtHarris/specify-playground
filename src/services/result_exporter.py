"""
ResultExporter service for exporting scan results to various formats.

This service handles exporting scan results to JSON and YAML formats
with proper error handling and validation.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any
import errno

from ..models.scan_result import ScanResult


class DiskSpaceError(Exception):
    """Raised when there is insufficient disk space to write the output file."""
    pass


class ResultExporter:
    """Service for exporting scan results to various output formats."""
    
    def export_json(self, result: ScanResult, output_path: Path) -> None:
        """Export scan results to JSON format."""
        data = self._prepare_export_data(result)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            if e.errno == 28:  # ENOSPC - No space left on device
                raise DiskSpaceError(f"Insufficient disk space to write {output_path}") from e
            elif e.errno == 13:  # EACCES - Permission denied
                raise PermissionError(f"Cannot write to {output_path}: Permission denied") from e
            else:
                raise
    
    def export_yaml(self, result: ScanResult, output_path: Path) -> None:
        """Export scan results to YAML format with flatter structure."""
        data = self._prepare_yaml_export_data(result)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
        except OSError as e:
            if e.errno == 28:  # ENOSPC - No space left on device
                raise DiskSpaceError(f"Insufficient disk space to write {output_path}") from e
            elif e.errno == 13:  # EACCES - Permission denied
                raise PermissionError(f"Cannot write to {output_path}: Permission denied") from e
            else:
                raise
    
    def _prepare_yaml_export_data(self, result: ScanResult) -> Dict[str, Any]:
        """Prepare scan result data for YAML export with flatter structure."""
        return {
            "version": "1.0.0",
            "metadata": {
                "scan_date": result.metadata.start_time.isoformat() if result.metadata.start_time else None,
                "scanned_directory": str(result.metadata.scan_paths[0]) if result.metadata.scan_paths else None,
                "duration_seconds": result.metadata.duration_seconds,
                "total_files_found": result.metadata.total_files_found,
                "total_files_processed": result.metadata.total_files_processed,
                "recursive": result.metadata.recursive,
                "errors": result.metadata.errors if result.metadata.errors else []
            },
            "duplicate_groups": [
                {
                    "group_id": group.hash_value,
                    "file_count": len(group.files),
                    "total_size_bytes": group.total_size,
                    "total_size_human": self._format_file_size(group.total_size),
                    "space_wasted_bytes": group.wasted_space,
                    "space_wasted_human": self._format_file_size(group.wasted_space),
                    "files": [
                        {
                            "path": str(file.path),
                            "size_bytes": file.size,
                            "size_human": self._format_file_size(file.size),
                            "hash": file.hash if hasattr(file, '_hash') and file._hash else None
                        }
                        for file in group.files
                    ]
                }
                for group in result.duplicate_groups
            ],
            "potential_matches": [
                {
                    "group_id": group.base_name,
                    "similarity_score": group.average_similarity,
                    "files": [
                        {
                            "path": str(file.path),
                            "size_bytes": file.size,
                            "size_human": self._format_file_size(file.size)
                        }
                        for file in group.files
                    ]
                }
                for group in result.potential_match_groups
            ]
        }
    
    def _prepare_export_data(self, result: ScanResult) -> Dict[str, Any]:
        """Prepare scan result data for JSON export with nested structure."""
        return {
            "version": "1.0.0",
            "metadata": {
                "scan_date": result.metadata.start_time.isoformat() if result.metadata.start_time else None,
                "scanned_directory": str(result.metadata.scan_paths[0]) if result.metadata.scan_paths else None,
                "duration_seconds": result.metadata.duration_seconds,
                "total_files_found": result.metadata.total_files_found,
                "total_files_processed": result.metadata.total_files_processed,
                "recursive": result.metadata.recursive,
                "errors": result.metadata.errors if result.metadata.errors else []
            },
            "results": {
                "duplicate_groups": [
                    {
                        "group_id": group.hash_value,
                        "file_count": len(group.files),
                        "total_size_bytes": group.total_size,
                        "total_size_human": self._format_file_size(group.total_size),
                        "space_wasted_bytes": group.wasted_space,
                        "space_wasted_human": self._format_file_size(group.wasted_space),
                        "files": [
                            {
                                "path": str(file.path),
                                "size_bytes": file.size,
                                "size_human": self._format_file_size(file.size),
                                "hash": file.hash if hasattr(file, '_hash') and file._hash else None
                            }
                            for file in group.files
                        ]
                    }
                    for group in result.duplicate_groups
                ],
                "potential_matches": [
                    {
                        "group_id": group.base_name,
                        "similarity_score": group.average_similarity,
                        "files": [
                            {
                                "path": str(file.path),
                                "size_bytes": file.size,
                                "size_human": self._format_file_size(file.size)
                            }
                            for file in group.files
                        ]
                    }
                    for group in result.potential_match_groups
                ],
                "statistics": {
                    "total_duplicate_groups": len(result.duplicate_groups),
                    "total_duplicate_files": sum(len(group.files) for group in result.duplicate_groups),
                    "total_wasted_space_bytes": sum(group.wasted_space for group in result.duplicate_groups),
                    "total_wasted_space_human": self._format_file_size(sum(group.wasted_space for group in result.duplicate_groups)),
                    "total_potential_match_groups": len(result.potential_match_groups),
                    "space_savings_potential_bytes": sum(group.wasted_space for group in result.duplicate_groups),
                    "space_savings_potential_human": self._format_file_size(sum(group.wasted_space for group in result.duplicate_groups))
                }
            }
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"