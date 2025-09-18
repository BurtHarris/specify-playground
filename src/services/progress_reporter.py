"""
ProgressReporter service for displaying progress during long-running operations.

This service provides progress tracking and display functionality
with support for TTY detection and terminal resize handling.
"""

import sys
import time
import os
from typing import Optional


class ProgressReporter:
    """Service for reporting progress during long-running operations."""
    
    def __init__(self, enabled: bool = None):
        """
        Initialize the ProgressReporter.
        
        Args:
            enabled: Whether progress reporting is enabled. If None, will be
                    auto-detected based on TTY status and CLI options.
        """
        self._enabled = enabled
        self._total_items = 0
        self._current_item = 0
        self._label = ""
        self._start_time = 0.0
        self._last_update_time = 0.0
        self._terminal_width = 80  # Default terminal width
        self._is_active = False
        
        # Auto-detect if not explicitly set
        if self._enabled is None:
            self._enabled = self._should_show_progress()
        
        # Update terminal width if we can
        self._update_terminal_width()
    
    def start_progress(self, total_items: int, label: str) -> None:
        """
        Initializes progress tracking.
        
        Args:
            total_items: Total number of items to process
            label: Description of the operation
            
        Contract:
            - MUST display progress bar if stdout is a TTY
            - MUST respect --no-progress CLI option
            - MUST handle terminal resize gracefully
        """
        if not self._enabled or total_items <= 0:
            return
        
        self._total_items = total_items
        self._current_item = 0
        self._label = label
        self._start_time = time.time()
        self._last_update_time = self._start_time
        self._is_active = True
        
        # Update terminal width
        self._update_terminal_width()
        
        # Show initial progress
        self._display_progress()
    
    def update_progress(self, current_item: int, current_file: str = None) -> None:
        """
        Updates progress display.
        
        Args:
            current_item: Current item number (1-based)
            current_file: Optional current file being processed
            
        Contract:
            - MUST update display without excessive CPU usage
            - MUST truncate long filenames to fit terminal width
            - MUST show percentage and estimated time remaining
        """
        if not self._enabled or not self._is_active:
            return
        
        self._current_item = current_item
        current_time = time.time()
        
        # Throttle updates to avoid excessive CPU usage (max 10 updates per second)
        if current_time - self._last_update_time < 0.1:
            return
        
        self._last_update_time = current_time
        
        # Update terminal width in case of resize
        self._update_terminal_width()
        
        # Display progress with optional current file
        self._display_progress(current_file)
    
    def finish_progress(self) -> None:
        """
        Completes progress tracking.
        
        Contract:
            - MUST clear progress bar when complete
            - MUST restore normal output mode
        """
        if not self._enabled or not self._is_active:
            return
        
        self._is_active = False
        
        # Clear the progress line
        if sys.stdout.isatty():
            sys.stdout.write('\r' + ' ' * self._terminal_width + '\r')
            sys.stdout.flush()
    
    def _should_show_progress(self) -> bool:
        """
        Determine if progress should be shown based on TTY status.
        
        Returns:
            True if progress should be displayed
        """
        # Don't show progress if stdout is not a TTY (e.g., redirected to file)
        return sys.stdout.isatty()
    
    def _update_terminal_width(self) -> None:
        """Update terminal width, handling resize gracefully."""
        try:
            # Try to get terminal size
            size = os.get_terminal_size()
            self._terminal_width = max(size.columns, 40)  # Minimum 40 chars
        except (OSError, AttributeError):
            # Fallback to default if terminal size can't be determined
            self._terminal_width = 80
    
    def _display_progress(self, current_file: str = None) -> None:
        """
        Display the progress bar with current status.
        
        Args:
            current_file: Optional current file being processed
        """
        if not sys.stdout.isatty():
            return
        
        # Calculate percentage
        if self._total_items > 0:
            percentage = min(100.0, (self._current_item / self._total_items) * 100)
        else:
            percentage = 0.0
        
        # Calculate elapsed and estimated time
        elapsed_time = time.time() - self._start_time
        if self._current_item > 0 and elapsed_time > 0:
            items_per_second = self._current_item / elapsed_time
            remaining_items = self._total_items - self._current_item
            if items_per_second > 0:
                eta_seconds = remaining_items / items_per_second
                eta_str = self._format_time(eta_seconds)
            else:
                eta_str = \"--:--\"\n        else:\n            eta_str = \"--:--\"\n        \n        # Build progress string\n        progress_info = f\"{self._label} {self._current_item}/{self._total_items} ({percentage:.1f}%) ETA: {eta_str}\"\n        \n        # Add current file if provided (truncate to fit)\n        if current_file:\n            available_width = self._terminal_width - len(progress_info) - 3  # Leave space for \" - \"\n            if available_width > 10:  # Only show if we have reasonable space\n                truncated_file = self._truncate_filename(current_file, available_width)\n                progress_info += f\" - {truncated_file}\"\n        \n        # Ensure the line doesn't exceed terminal width\n        if len(progress_info) > self._terminal_width:\n            progress_info = progress_info[:self._terminal_width - 3] + \"...\"\n        \n        # Display with carriage return to overwrite previous line\n        sys.stdout.write(f'\\r{progress_info}')\n        sys.stdout.flush()\n    \n    def _truncate_filename(self, filename: str, max_length: int) -> str:\n        \"\"\"\n        Truncate a filename to fit within the specified length.\n        \n        Args:\n            filename: The filename to truncate\n            max_length: Maximum allowed length\n            \n        Returns:\n            Truncated filename with ellipsis if necessary\n        \"\"\"\n        if len(filename) <= max_length:\n            return filename\n        \n        if max_length <= 3:\n            return \"...\"\n        \n        # Try to keep the end of the filename (usually more important)\n        return \"...\" + filename[-(max_length - 3):]\n    \n    def _format_time(self, seconds: float) -> str:\n        \"\"\"\n        Format time duration as MM:SS or HH:MM:SS.\n        \n        Args:\n            seconds: Time duration in seconds\n            \n        Returns:\n            Formatted time string\n        \"\"\"\n        if seconds < 0:\n            return \"--:--\"\n        \n        seconds = int(seconds)\n        hours = seconds // 3600\n        minutes = (seconds % 3600) // 60\n        secs = seconds % 60\n        \n        if hours > 0:\n            return f\"{hours:02d}:{minutes:02d}:{secs:02d}\"\n        else:\n            return f\"{minutes:02d}:{secs:02d}\"\n    \n    def set_enabled(self, enabled: bool) -> None:\n        \"\"\"\n        Enable or disable progress reporting.\n        \n        Args:\n            enabled: Whether to enable progress reporting\n        \"\"\"\n        self._enabled = enabled\n    \n    @property\n    def is_enabled(self) -> bool:\n        \"\"\"\n        Check if progress reporting is enabled.\n        \n        Returns:\n            True if progress reporting is enabled\n        \"\"\"\n        return self._enabled"