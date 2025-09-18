"""
Models package for Video Duplicate Scanner CLI.

Contains all data model classes for representing video files,
duplicate groups, potential matches, and scan results.
"""

from .video_file import VideoFile
from .duplicate_group import DuplicateGroup
from .potential_match_group import PotentialMatchGroup
from .scan_metadata import ScanMetadata
from .scan_result import ScanResult

__all__ = [
    'VideoFile',
    'DuplicateGroup', 
    'PotentialMatchGroup',
    'ScanMetadata',
    'ScanResult'
]