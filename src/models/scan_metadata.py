#!/usr/bin/env python3
"""
ScanMetadata model for Video Duplicate Scanner CLI.

Contains metadata about the scanning process including timing, statistics,
and configuration information.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set


class ScanMetadata:
    """Contains metadata about a video duplicate scanning operation."""
    
    def __init__(self, scan_paths: List[Path], recursive: bool = True):
        """
        Initialize scan metadata.
        
        Args:
            scan_paths: List of paths that were scanned
            recursive: Whether scanning was recursive
        """
        self.scan_paths = [Path(p).resolve() for p in scan_paths]
        self.recursive = recursive
        
        # Timing information
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Statistics
        self.total_files_found = 0
        self.total_files_processed = 0
        self.total_files_skipped = 0
        self.total_files_error = 0
        
        # Size information
        self.total_size_scanned = 0
        self.total_size_duplicates = 0
        self.total_size_wasted = 0
        
        # Hash computation statistics
        self.files_hashed = 0
        self.hash_computation_time = timedelta()
        
        # Error tracking
        self.errors: List[Dict[str, str]] = []
        self.skipped_files: List[Dict[str, str]] = []
        
        # Performance metrics
        self.directories_scanned = 0
        self.duplicate_groups_found = 0
        self.potential_match_groups_found = 0
        
        # Configuration
        self.supported_extensions: Set[str] = {'.mp4', '.mkv', '.mov'}
        self.similarity_threshold = 0.8
        self.hash_algorithm = 'blake2b'
    
    def start_scan(self) -> None:
        """Mark the start of the scanning process."""
        self.start_time = datetime.now()
    
    def end_scan(self) -> None:
        """Mark the end of the scanning process."""
        self.end_time = datetime.now()
    
    @property
    def duration(self) -> Optional[timedelta]:
        """
        Total duration of the scan.
        
        Returns:
            Duration as timedelta if scan completed, None if still running or not started
        """
        if self.start_time is None:
            return None
        
        end_time = self.end_time or datetime.now()
        return end_time - self.start_time
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """
        Total duration in seconds.
        
        Returns:
            Duration in seconds, None if not available
        """
        duration = self.duration
        return duration.total_seconds() if duration else None
    
    @property
    def is_running(self) -> bool:
        """True if scan is currently running (started but not ended)."""
        return self.start_time is not None and self.end_time is None
    
    @property
    def is_completed(self) -> bool:
        """True if scan has completed (both start and end times set)."""
        return self.start_time is not None and self.end_time is not None
    
    @property
    def files_per_second(self) -> Optional[float]:
        """
        Processing rate in files per second.
        
        Returns:
            Files per second, None if scan not completed or no duration
        """
        duration_sec = self.duration_seconds
        if duration_sec is None or duration_sec == 0:
            return None
        
        return self.total_files_processed / duration_sec
    
    @property
    def bytes_per_second(self) -> Optional[float]:
        """
        Processing rate in bytes per second.
        
        Returns:
            Bytes per second, None if scan not completed or no duration
        """
        duration_sec = self.duration_seconds
        if duration_sec is None or duration_sec == 0:
            return None
        
        return self.total_size_scanned / duration_sec
    
    @property
    def average_hash_time(self) -> Optional[float]:
        """
        Average time to compute hash per file in seconds.
        
        Returns:
            Average hash computation time per file, None if no files hashed
        """
        if self.files_hashed == 0:
            return None
        
        return self.hash_computation_time.total_seconds() / self.files_hashed
    
    @property
    def error_rate(self) -> float:
        """
        Percentage of files that encountered errors.
        
        Returns:
            Error rate as percentage (0.0-100.0)
        """
        if self.total_files_found == 0:
            return 0.0
        
        return (self.total_files_error / self.total_files_found) * 100.0
    
    @property
    def processing_rate(self) -> float:
        """
        Percentage of files successfully processed.
        
        Returns:
            Processing rate as percentage (0.0-100.0)
        """
        if self.total_files_found == 0:
            return 0.0
        
        return (self.total_files_processed / self.total_files_found) * 100.0
    
    @property
    def space_savings_potential(self) -> float:
        """
        Potential space savings as percentage of total scanned size.
        
        Returns:
            Space savings percentage (0.0-100.0)
        """
        if self.total_size_scanned == 0:
            return 0.0
        
        return (self.total_size_wasted / self.total_size_scanned) * 100.0
    
    def add_error(self, file_path: Path, error_message: str, error_type: str = "unknown") -> None:
        """
        Record an error encountered during scanning.
        
        Args:
            file_path: Path to file that caused error
            error_message: Description of the error
            error_type: Type of error (e.g., 'permission', 'io', 'format')
        """
        self.errors.append({
            'file_path': str(file_path),
            'error_message': error_message,
            'error_type': error_type,
            'timestamp': datetime.now().isoformat()
        })
        self.total_files_error += 1
    
    def add_skipped_file(self, file_path: Path, reason: str) -> None:
        """
        Record a file that was skipped during scanning.
        
        Args:
            file_path: Path to file that was skipped
            reason: Reason why file was skipped
        """
        self.skipped_files.append({
            'file_path': str(file_path),
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        self.total_files_skipped += 1
    
    def increment_processed(self, file_size: int = 0) -> None:
        """
        Increment processed file count and size.
        
        Args:
            file_size: Size of the processed file in bytes
        """
        self.total_files_processed += 1
        self.total_size_scanned += file_size
    
    def increment_hashed(self, hash_time: timedelta) -> None:
        """
        Increment hashed file count and total hash computation time.
        
        Args:
            hash_time: Time taken to compute the hash
        """
        self.files_hashed += 1
        self.hash_computation_time += hash_time
    
    def update_duplicate_stats(self, duplicate_size: int, wasted_size: int) -> None:
        """
        Update duplicate-related statistics.
        
        Args:
            duplicate_size: Total size of duplicate files
            wasted_size: Size of wasted space (duplicates minus one copy)
        """
        self.total_size_duplicates += duplicate_size
        self.total_size_wasted += wasted_size
    
    def get_summary_stats(self) -> Dict[str, any]:
        """
        Get a summary of key statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'total_files_found': self.total_files_found,
            'total_files_processed': self.total_files_processed,
            'total_files_skipped': self.total_files_skipped,
            'total_files_error': self.total_files_error,
            'processing_rate_percent': round(self.processing_rate, 1),
            'error_rate_percent': round(self.error_rate, 1),
            'total_size_scanned_mb': round(self.total_size_scanned / (1024 * 1024), 2),
            'total_size_wasted_mb': round(self.total_size_wasted / (1024 * 1024), 2),
            'space_savings_potential_percent': round(self.space_savings_potential, 1),
            'duplicate_groups_found': self.duplicate_groups_found,
            'potential_match_groups_found': self.potential_match_groups_found,
            'duration_seconds': self.duration_seconds,
            'files_per_second': round(self.files_per_second or 0, 2),
            'mb_per_second': round((self.bytes_per_second or 0) / (1024 * 1024), 2)
        }
    
    def get_performance_stats(self) -> Dict[str, any]:
        """
        Get detailed performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            'scan_duration_seconds': self.duration_seconds,
            'files_per_second': self.files_per_second,
            'bytes_per_second': self.bytes_per_second,
            'mb_per_second': (self.bytes_per_second or 0) / (1024 * 1024),
            'average_hash_time_seconds': self.average_hash_time,
            'total_hash_time_seconds': self.hash_computation_time.total_seconds(),
            'hash_percentage_of_total': (
                (self.hash_computation_time.total_seconds() / (self.duration_seconds or 1)) * 100
                if self.duration_seconds else 0
            )
        }
    
    def __str__(self) -> str:
        """String representation with key statistics."""
        status = "running" if self.is_running else "completed" if self.is_completed else "not started"
        
        return (
            f"ScanMetadata(status={status}, "
            f"files_processed={self.total_files_processed}, "
            f"duplicates_found={self.duplicate_groups_found})"
        )
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"ScanMetadata(scan_paths={len(self.scan_paths)}, "
            f"recursive={self.recursive}, "
            f"files_processed={self.total_files_processed}, "
            f"files_error={self.total_files_error}, "
            f"duration={self.duration})"
        )
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation for JSON/YAML export.
        
        Returns:
            Dictionary with all metadata
        """
        return {
            'scan_configuration': {
                'scan_paths': [str(p) for p in self.scan_paths],
                'recursive': self.recursive,
                'supported_extensions': sorted(self.supported_extensions),
                'similarity_threshold': self.similarity_threshold,
                'hash_algorithm': self.hash_algorithm
            },
            'timing': {
                'start_time': self.start_time.isoformat() + 'Z' if self.start_time else None,
                'end_time': self.end_time.isoformat() + 'Z' if self.end_time else None,
                'duration_seconds': self.duration_seconds,
                'status': 'running' if self.is_running else 'completed' if self.is_completed else 'not_started'
            },
            'file_statistics': {
                'total_files_found': self.total_files_found,
                'total_files_processed': self.total_files_processed,
                'total_files_skipped': self.total_files_skipped,
                'total_files_error': self.total_files_error,
                'processing_rate_percent': round(self.processing_rate, 1),
                'error_rate_percent': round(self.error_rate, 1)
            },
            'size_statistics': {
                'total_size_scanned': self.total_size_scanned,
                'total_size_duplicates': self.total_size_duplicates,
                'total_size_wasted': self.total_size_wasted,
                'space_savings_potential_percent': round(self.space_savings_potential, 1)
            },
            'performance_metrics': self.get_performance_stats(),
            'duplicate_detection': {
                'duplicate_groups_found': self.duplicate_groups_found,
                'potential_match_groups_found': self.potential_match_groups_found,
                'files_hashed': self.files_hashed,
                'hash_computation_time_seconds': self.hash_computation_time.total_seconds(),
                'average_hash_time_seconds': self.average_hash_time
            },
            'errors': self.errors,
            'skipped_files': self.skipped_files
        }