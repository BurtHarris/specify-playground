"""
OneDrive cloud file status enumeration.

This module defines the CloudFileStatus enum for OneDrive Integration MVP.
Supports LOCAL and CLOUD_ONLY states for Windows file attribute detection.
"""

from enum import Enum


class CloudFileStatus(Enum):
    """
    OneDrive cloud file status enumeration.
    
    Represents the cloud status of a file in OneDrive integration:
    - LOCAL: File is fully available locally (can be processed normally)
    - CLOUD_ONLY: File is cloud-only (should be skipped during processing)
    
    This enum is used for MVP scope with Windows file attribute detection only.
    Future enhancements may add additional states like AVAILABLE, PINNED, etc.
    """
    
    LOCAL = "local"
    """File is fully available locally and can be processed normally."""
    
    CLOUD_ONLY = "cloud_only" 
    """File is cloud-only (OneDrive stub) and should be skipped during processing."""
    
    def __str__(self) -> str:
        """Return string representation matching enum format."""
        return f"CloudFileStatus.{self.name}"
    
    def __repr__(self) -> str:
        """Return detailed string representation for debugging."""
        return f"CloudFileStatus.{self.name}"
    
    @classmethod
    def from_string(cls, value: str) -> "CloudFileStatus":
        """
        Create CloudFileStatus from string value.
        
        Args:
            value: String value ("local" or "cloud_only")
            
        Returns:
            CloudFileStatus enum value
            
        Raises:
            ValueError: If value is not a valid CloudFileStatus
        """
        # Normalize input - handle case variations and dashes
        normalized = value.lower().replace("-", "_").strip()
        
        for status in cls:
            if status.value == normalized:
                return status
                
        raise ValueError(f"Invalid CloudFileStatus value: {value}")
    
    @property
    def is_local(self) -> bool:
        """Check if this status represents a locally available file."""
        return self == CloudFileStatus.LOCAL
    
    @property 
    def is_cloud_only(self) -> bool:
        """Check if this status represents a cloud-only file."""
        return self == CloudFileStatus.CLOUD_ONLY
    
    @property
    def can_process(self) -> bool:
        """Check if files with this status can be processed (hashed, scanned)."""
        return self.is_local
    
    @property
    def should_skip(self) -> bool:
        """Check if files with this status should be skipped during scanning."""
        return self.is_cloud_only