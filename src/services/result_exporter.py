"""
ResultExporter service for exporting scan results to YAML format.

This service handles exporting scan results to YAML format
with proper error handling and validation.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
 

from ..models.scan_result import ScanResult


class DiskSpaceError(Exception):
    """Raised when there is insufficient disk space to write the output file."""

    pass


class ResultExporter:
    """Service for exporting scan results to YAML format."""

    def export_yaml(self, result: ScanResult, output_path: Path) -> None:
        """Export scan results to YAML format with flatter structure."""
        data = self._prepare_yaml_export_data(result)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )
        except OSError as e:
            if e.errno == 28:  # ENOSPC - No space left on device
                raise DiskSpaceError(
                    f"Insufficient disk space to write {output_path}"
                ) from e
            elif e.errno == 13:  # EACCES - Permission denied
                raise PermissionError(
                    f"Cannot write to {output_path}: Permission denied"
                ) from e
            else:
                raise

    def _prepare_yaml_export_data(self, result: ScanResult) -> Dict[str, Any]:
        """Prepare scan result data for YAML export with flatter structure."""
        data = {
            "version": "1.0.0",
            "metadata": {
                "scan_date": result.metadata.start_time.isoformat()
                if result.metadata.start_time
                else None,
                "scanned_directory": str(result.metadata.scan_paths[0])
                if result.metadata.scan_paths
                else None,
                "duration_seconds": result.metadata.duration_seconds,
                "total_files_found": result.metadata.total_files_found,
                "total_files_processed": result.metadata.total_files_processed,
                "recursive": result.metadata.recursive,
                # Keep `errors` present to satisfy contract tests; it may be an empty list
                "errors": result.metadata.errors if result.metadata.errors is not None else [],
                # Series detection summary (optional)
                "series_groups_found": getattr(
                    result.metadata, "series_groups_found", 0
                ),
                "series_groups": getattr(result.metadata, "series_groups", []),
            },
            "duplicate_groups": [
                {
                    "group_id": group.hash_value,
                    "file_count": len(group.files),
                    "total_size_bytes": group.total_size,
                    "total_size_human": self._format_file_size(
                        group.total_size
                    ),
                    "space_wasted_bytes": group.wasted_space,
                    "space_wasted_human": self._format_file_size(
                        group.wasted_space
                    ),
                    "files": [
                        {
                            "path": str(file.path),
                            "size_bytes": file.size,
                            "size_human": self._format_file_size(file.size),
                            "hash": file.hash
                            if hasattr(file, "_hash") and file._hash
                            else None,
                        }
                        for file in group.files
                    ],
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
                            "size_human": self._format_file_size(file.size),
                        }
                        for file in group.files
                    ],
                }
                for group in result.potential_match_groups
            ],
        }

        # Omit empty-list metadata keys to reduce clutter in the YAML export.
        # Tests expect minimal use of inline bracket notation for empty lists,
        # so remove optional keys when they are empty.
        try:
            meta = data.get("metadata", {})
            # Always keep `errors` present (may be empty) to satisfy contract tests.
            # Only omit the detailed `series_groups` list when empty to reduce
            # YAML clutter.
            if isinstance(meta.get("series_groups"), list) and len(meta["series_groups"]) == 0:
                del meta["series_groups"]
        except Exception:
            # Non-critical: avoid letting export preparation fail on metadata shaping
            pass

        return data

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

    def export_json(self, result: ScanResult, output_path: Path) -> None:
        raise NotImplementedError(
            "JSON export has been removed; use YAML export (export_yaml) instead"
        )
