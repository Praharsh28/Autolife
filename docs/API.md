# Autolife Media Processing Application - API Documentation

## Core Components

### SubtitleSynchronizer

The `SubtitleSynchronizer` class provides intelligent subtitle synchronization between original and translated subtitles.

```python
from modules.utils.sync_utils import SubtitleSynchronizer

sync = SubtitleSynchronizer()
```

#### Methods

##### find_sync_points
```python
def find_sync_points(original: List[Dict], translated: List[Dict]) -> List[SyncPoint]
```
Finds synchronization points between original and translated subtitles.

Parameters:
- `original`: List of original subtitle dictionaries
- `translated`: List of translated subtitle dictionaries

Returns:
- List of `SyncPoint` objects containing timing correlations

##### calculate_transform
```python
def calculate_transform() -> Tuple[float, float]
```
Calculates time scale and offset for synchronization.

Returns:
- Tuple of (scale, offset) for timing adjustments

##### apply_sync
```python
def apply_sync(subtitles: List[Dict]) -> List[Dict]
```
Applies synchronization to subtitles.

Parameters:
- `subtitles`: List of subtitle dictionaries to synchronize

Returns:
- List of synchronized subtitle dictionaries

### BatchManager

The `BatchManager` class handles concurrent processing of multiple media files.

```python
from modules.processing.batch_manager import BatchManager

manager = BatchManager(max_concurrent=2)
```

#### Methods

##### add_task
```python
def add_task(file_path: Path, target_languages: List[str]) -> str
```
Adds a new processing task.

Parameters:
- `file_path`: Path to media file
- `target_languages`: List of target language codes

Returns:
- Task ID string

##### start_processing
```python
def start_processing()
```
Starts batch processing of queued tasks.

##### stop_processing
```python
def stop_processing()
```
Stops all processing and cancels pending tasks.

##### cancel_task
```python
def cancel_task(task_id: str)
```
Cancels a specific task.

Parameters:
- `task_id`: ID of task to cancel

##### get_task_status
```python
def get_task_status(task_id: str) -> Optional[ProcessingTask]
```
Gets status of a specific task.

Parameters:
- `task_id`: ID of task to check

Returns:
- `ProcessingTask` object or None if not found

## Data Types

### SyncPoint
```python
@dataclass
class SyncPoint:
    original_time: float
    translated_time: float
    confidence: float
```

### ProcessingTask
```python
@dataclass
class ProcessingTask:
    file_path: Path
    target_languages: List[str]
    status: ProcessingStatus
    error: Optional[str] = None
    progress: float = 0.0
    result: Optional[Dict] = None
```

### ProcessingStatus
```python
class ProcessingStatus(Enum):
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
```

## Events

### BatchManager Events

#### on_task_complete
```python
def on_task_complete(task_id: str, task: ProcessingTask)
```
Called when a task completes successfully.

#### on_task_error
```python
def on_task_error(task_id: str, error: str)
```
Called when a task fails with an error.

#### on_progress_update
```python
def on_progress_update(task_id: str, progress: float)
```
Called when task progress updates.

## Usage Examples

### Synchronizing Subtitles
```python
# Initialize synchronizer
sync = SubtitleSynchronizer()

# Find sync points
sync_points = sync.find_sync_points(original_subs, translated_subs)

# Calculate and apply transformation
scale, offset = sync.calculate_transform()
synced_subs = sync.apply_sync(translated_subs)
```

### Batch Processing
```python
# Initialize manager
manager = BatchManager(max_concurrent=2)

# Add callback handlers
manager.on_task_complete = lambda task_id, task: print(f"Task {task_id} completed")
manager.on_task_error = lambda task_id, error: print(f"Task {task_id} failed: {error}")
manager.on_progress_update = lambda task_id, progress: print(f"Task {task_id}: {progress:.1%}")

# Add and process tasks
task_id = manager.add_task(video_path, ['es', 'fr', 'de'])
manager.start_processing()

# Monitor specific task
task = manager.get_task_status(task_id)
print(f"Task status: {task.status}")
```

## Error Handling

The API uses exceptions to indicate errors:

- `ValueError`: Invalid parameter values
- `RuntimeError`: Processing or system errors
- `IOError`: File access errors

Example error handling:
```python
try:
    manager.add_task(file_path, languages)
except ValueError as e:
    print(f"Invalid parameters: {e}")
except RuntimeError as e:
    print(f"Processing error: {e}")
except IOError as e:
    print(f"File error: {e}")
```

## Best Practices

1. **Resource Management**
   - Limit concurrent tasks based on system resources
   - Clean up resources with `stop_processing()`
   - Monitor disk space usage

2. **Error Handling**
   - Always handle potential exceptions
   - Provide meaningful error messages
   - Implement proper cleanup

3. **Performance**
   - Batch similar tasks together
   - Reuse synchronizer instances
   - Cache results when appropriate

4. **Testing**
   - Unit test all components
   - Test edge cases and errors
   - Verify cleanup procedures
