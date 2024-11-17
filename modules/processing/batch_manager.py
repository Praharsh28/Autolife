"""Batch processing manager for media files."""

from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path
import logging
from typing import List, Dict, Any
from enum import Enum, auto

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()

class ProcessingTask:
    """Represents a processing task with state management."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.status = ProcessingStatus.PENDING
        self.error = None
        self.progress = 0
        self.result = None
    
    def update_progress(self, value: int):
        """Update task progress."""
        self.progress = max(0, min(100, value))
    
    def mark_completed(self, result: Any = None):
        """Mark task as completed."""
        self.status = ProcessingStatus.COMPLETED
        self.progress = 100
        self.result = result
    
    def mark_failed(self, error: str):
        """Mark task as failed with error."""
        self.status = ProcessingStatus.FAILED
        self.error = error
    
    def mark_cancelled(self):
        """Mark task as cancelled."""
        self.status = ProcessingStatus.CANCELLED

class BatchManager(QObject):
    """Manages batch processing of media files."""
    
    # Signals
    job_started = pyqtSignal(str)  # file_path
    job_completed = pyqtSignal(str)  # file_path
    job_failed = pyqtSignal(str, str)  # file_path, error
    job_cancelled = pyqtSignal(str)  # file_path
    progress_updated = pyqtSignal(str, int)  # file_path, progress
    batch_completed = pyqtSignal()
    
    def __init__(self, max_concurrent: int = 4):
        super().__init__()
        self.max_concurrent = max_concurrent
        self._tasks: Dict[str, ProcessingTask] = {}
        self._active_tasks: Dict[str, ProcessingTask] = {}
        self._is_processing = False
        self._initialize()
    
    def _initialize(self):
        """Initialize batch manager state."""
        self._tasks.clear()
        self._active_tasks.clear()
        self._is_processing = False
    
    def add_files(self, files: List[str]) -> int:
        """Add files to processing queue with validation."""
        added_count = 0
        for file in files:
            if self._validate_file(file):
                self._tasks[file] = ProcessingTask(file)
                added_count += 1
            else:
                logger.warning(f"Invalid file skipped: {file}")
        return added_count
    
    def _validate_file(self, file: str) -> bool:
        """Validate file for processing."""
        if not file or not Path(file).exists():
            return False
        if file in self._tasks:
            return False
        return True
    
    def process_files(self, files: List[str] = None):
        """Start processing files with proper state management."""
        if files:
            self.add_files(files)
        
        if not self._tasks:
            logger.warning("No valid files to process")
            self.batch_completed.emit()
            return
        
        self._is_processing = True
        self._process_next_batch()
    
    def _process_next_batch(self):
        """Process next batch of files."""
        if not self._is_processing:
            return
            
        while len(self._active_tasks) < self.max_concurrent:
            next_task = self._get_next_pending_task()
            if not next_task:
                break
                
            self._start_task(next_task)
    
    def _get_next_pending_task(self) -> ProcessingTask:
        """Get next pending task."""
        for task in self._tasks.values():
            if task.status == ProcessingStatus.PENDING:
                return task
        return None
    
    def _start_task(self, task: ProcessingTask):
        """Start processing a task."""
        task.status = ProcessingStatus.PROCESSING
        self._active_tasks[task.file_path] = task
        self.job_started.emit(task.file_path)
        
        # Start processing in worker thread
        # Implement actual processing logic
    
    def _on_task_completed(self, file_path: str, result: Any = None):
        """Handle task completion."""
        if file_path in self._active_tasks:
            task = self._active_tasks[file_path]
            task.mark_completed(result)
            self._cleanup_task(task)
            self.job_completed.emit(file_path)
            self._process_next_batch()
    
    def _on_task_failed(self, file_path: str, error: str):
        """Handle task failure."""
        if file_path in self._active_tasks:
            task = self._active_tasks[file_path]
            task.mark_failed(error)
            self._cleanup_task(task)
            self.job_failed.emit(file_path, error)
            self._process_next_batch()
    
    def _cleanup_task(self, task: ProcessingTask):
        """Clean up completed or failed task."""
        if task.file_path in self._active_tasks:
            del self._active_tasks[task.file_path]
        
        if not self._active_tasks and self._is_processing:
            self._on_batch_completed()
    
    def _on_batch_completed(self):
        """Handle batch completion."""
        self._is_processing = False
        self.batch_completed.emit()
    
    def stop_processing(self):
        """Stop all processing."""
        self._is_processing = False
        for task in self._active_tasks.values():
            task.mark_cancelled()
            self.job_cancelled.emit(task.file_path)
        self._active_tasks.clear()
    
    def get_status(self, file_path: str) -> ProcessingStatus:
        """Get processing status for a file."""
        return self._tasks[file_path].status if file_path in self._tasks else None
    
    def get_progress(self, file_path: str) -> int:
        """Get processing progress for a file."""
        return self._tasks[file_path].progress if file_path in self._tasks else 0
    
    def get_error(self, file_path: str) -> str:
        """Get error message for a failed file."""
        return self._tasks[file_path].error if file_path in self._tasks else None
    
    @property
    def is_processing(self) -> bool:
        """Check if batch processing is active."""
        return self._is_processing
    
    @property
    def active_jobs(self) -> int:
        """Get number of active jobs."""
        return len(self._active_tasks)
    
    @property
    def pending_jobs(self) -> int:
        """Get number of pending jobs."""
        return sum(1 for task in self._tasks.values() 
                  if task.status == ProcessingStatus.PENDING)
    
    @property
    def completed_jobs(self) -> int:
        """Get number of completed jobs."""
        return sum(1 for task in self._tasks.values() 
                  if task.status == ProcessingStatus.COMPLETED)
    
    @property
    def failed_jobs(self) -> int:
        """Get number of failed jobs."""
        return sum(1 for task in self._tasks.values() 
                  if task.status == ProcessingStatus.FAILED)
