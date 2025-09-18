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
        """Initialize the ProgressReporter."""
        self._enabled = enabled
        self._total_items = 0
        self._current_item = 0
        self._label = ""
        self._start_time = 0.0
        self._last_update_time = 0.0
        self._terminal_width = 80
        self._is_active = False
        
        if self._enabled is None:
            self._enabled = self._should_show_progress()
        
        self._update_terminal_width()
    
    def start_progress(self, total_items: int, label: str) -> None:
        """Initialize progress tracking."""
        if not self._enabled or total_items <= 0:
            return
        
        self._total_items = total_items
        self._current_item = 0
        self._label = label
        self._start_time = time.time()
        self._last_update_time = self._start_time
        self._is_active = True
        
        self._update_terminal_width()
        self._display_progress()
    
    def update_progress(self, current_item: int, current_file: str = None) -> None:
        """Update progress display."""
        if not self._enabled or not self._is_active:
            return
        
        self._current_item = current_item
        current_time = time.time()
        
        if current_time - self._last_update_time < 0.1:
            return
        
        self._last_update_time = current_time
        self._update_terminal_width()
        self._display_progress(current_file)
    
    def finish_progress(self) -> None:
        """Complete progress tracking."""
        if not self._enabled or not self._is_active:
            return
        
        self._is_active = False
        
        if sys.stdout.isatty():
            sys.stdout.write('\r' + ' ' * self._terminal_width + '\r')
            sys.stdout.flush()
    
    def _should_show_progress(self) -> bool:
        """Determine if progress should be shown."""
        return sys.stdout.isatty()
    
    def _update_terminal_width(self) -> None:
        """Update terminal width."""
        try:
            size = os.get_terminal_size()
            self._terminal_width = max(size.columns, 40)
        except (OSError, AttributeError):
            self._terminal_width = 80
    
    def _display_progress(self, current_file: str = None) -> None:
        """Display the progress bar."""
        if not sys.stdout.isatty():
            return
        
        if self._total_items > 0:
            percentage = min(100.0, (self._current_item / self._total_items) * 100)
        else:
            percentage = 0.0
        
        elapsed_time = time.time() - self._start_time
        if self._current_item > 0 and elapsed_time > 0:
            items_per_second = self._current_item / elapsed_time
            remaining_items = self._total_items - self._current_item
            if items_per_second > 0:
                eta_seconds = remaining_items / items_per_second
                eta_str = self._format_time(eta_seconds)
            else:
                eta_str = "--:--"
        else:
            eta_str = "--:--"
        
        progress_info = f"{self._label} {self._current_item}/{self._total_items} ({percentage:.1f}%) ETA: {eta_str}"
        
        if current_file:
            available_width = self._terminal_width - len(progress_info) - 3
            if available_width > 10:
                truncated_file = self._truncate_filename(current_file, available_width)
                progress_info += f" - {truncated_file}"
        
        if len(progress_info) > self._terminal_width:
            progress_info = progress_info[:self._terminal_width - 3] + "..."
        
        sys.stdout.write(f'\r{progress_info}')
        sys.stdout.flush()
    
    def _truncate_filename(self, filename: str, max_length: int) -> str:
        """Truncate a filename to fit within the specified length."""
        if len(filename) <= max_length:
            return filename
        
        if max_length <= 3:
            return "..."
        
        return "..." + filename[-(max_length - 3):]
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration as MM:SS or HH:MM:SS."""
        if seconds < 0:
            return "--:--"
        
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable progress reporting."""
        self._enabled = enabled
    
    @property
    def is_enabled(self) -> bool:
        """Check if progress reporting is enabled."""
        return self._enabled