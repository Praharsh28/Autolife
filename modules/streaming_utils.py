"""
Streaming utilities for efficient processing of large media files.
"""

import os
import time
import tempfile
import threading
from typing import Generator, Optional, List, Dict, BinaryIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from .utilities import setup_logger
from .disk_utils import check_disk_space, estimate_space_needed
from .ffmpeg_utils import FFmpegProcess, FFmpegError
from .constants import (
    CHUNK_SIZE, MAX_CHUNK_DURATION, CHUNK_OVERLAP,
    MIN_CHUNK_SIZE, MAX_CHUNKS_IN_MEMORY,
    STREAM_BUFFER_SIZE, MAX_PARALLEL_CHUNKS
)

logger = setup_logger('streaming_utils')

class StreamingError(Exception):
    """Base exception for streaming-related errors."""
    pass

class AudioChunk:
    """Class representing a chunk of audio data."""
    
    def __init__(
        self,
        start_time: float,
        duration: float,
        file_path: Optional[str] = None,
        data: Optional[bytes] = None
    ):
        """
        Initialize audio chunk.
        
        Args:
            start_time: Start time in seconds
            duration: Duration in seconds
            file_path: Optional path to chunk file
            data: Optional chunk data in memory
        """
        self.start_time = start_time
        self.duration = duration
        self.file_path = file_path
        self.data = data
        self._temp_file: Optional[str] = None
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
        
    def cleanup(self):
        """Clean up temporary files."""
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
                self._temp_file = None
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {str(e)}")
                
    def to_file(self) -> str:
        """
        Save chunk data to temporary file if not already on disk.
        
        Returns:
            str: Path to chunk file
        """
        if self.file_path:
            return self.file_path
            
        if not self.data:
            raise StreamingError("No data available for chunk")
            
        if not self._temp_file:
            fd, self._temp_file = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            with open(self._temp_file, 'wb') as f:
                f.write(self.data)
                
        return self._temp_file
        
    def to_memory(self) -> bytes:
        """
        Load chunk data into memory if not already there.
        
        Returns:
            bytes: Chunk data
        """
        if self.data:
            return self.data
            
        if not self.file_path:
            raise StreamingError("No file available for chunk")
            
        with open(self.file_path, 'rb') as f:
            self.data = f.read()
            
        return self.data

class AudioStreamer:
    """Class for streaming large audio files in chunks."""
    
    def __init__(self, file_path: str):
        """
        Initialize audio streamer.
        
        Args:
            file_path: Path to audio file
        """
        self.file_path = file_path
        self.ffmpeg = FFmpegProcess(file_path)
        self.duration = self.ffmpeg.get_duration()
        if not self.duration:
            raise StreamingError("Could not determine file duration")
            
        self.chunk_size = self._calculate_chunk_size()
        self.chunks_processed = 0
        self.total_chunks = self._calculate_total_chunks()
        self._stop_flag = False
        self.logger = setup_logger(f'AudioStreamer_{os.path.basename(file_path)}')
        
    def _calculate_chunk_size(self) -> float:
        """Calculate optimal chunk size based on file size and duration."""
        try:
            file_size = os.path.getsize(self.file_path)
            size_based = max(MIN_CHUNK_SIZE, file_size / MAX_CHUNKS_IN_MEMORY)
            time_based = min(MAX_CHUNK_DURATION, self.duration / MAX_PARALLEL_CHUNKS)
            return min(size_based, time_based)
        except Exception as e:
            self.logger.error(f"Error calculating chunk size: {str(e)}")
            return MAX_CHUNK_DURATION
            
    def _calculate_total_chunks(self) -> int:
        """Calculate total number of chunks."""
        return max(1, int(self.duration / self.chunk_size))
        
    def stream_chunks(
        self,
        chunk_callback=None,
        progress_callback=None
    ) -> Generator[AudioChunk, None, None]:
        """
        Stream audio file in chunks.
        
        Args:
            chunk_callback: Optional callback for each chunk
            progress_callback: Optional callback for progress updates
            
        Yields:
            AudioChunk: Next chunk of audio
        """
        try:
            chunk_duration = self.chunk_size
            overlap = CHUNK_OVERLAP
            
            for chunk_index in range(self.total_chunks):
                if self._stop_flag:
                    break
                    
                start_time = chunk_index * (chunk_duration - overlap)
                is_last_chunk = chunk_index == self.total_chunks - 1
                
                if is_last_chunk:
                    actual_duration = self.duration - start_time
                else:
                    actual_duration = chunk_duration
                    
                # Create temporary file for chunk
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    chunk_path = temp_file.name
                    
                try:
                    # Extract chunk
                    success = self.ffmpeg.extract_audio_chunk(
                        self.file_path,
                        chunk_path,
                        start_time,
                        actual_duration
                    )
                    
                    if not success:
                        raise StreamingError(f"Failed to extract chunk {chunk_index}")
                        
                    chunk = AudioChunk(
                        start_time=start_time,
                        duration=actual_duration,
                        file_path=chunk_path
                    )
                    
                    if chunk_callback:
                        chunk_callback(chunk)
                        
                    self.chunks_processed += 1
                    if progress_callback:
                        progress = (self.chunks_processed / self.total_chunks) * 100
                        progress_callback(progress)
                        
                    yield chunk
                    
                finally:
                    # Cleanup temporary file
                    try:
                        if os.path.exists(chunk_path):
                            os.remove(chunk_path)
                    except Exception as e:
                        self.logger.warning(f"Failed to cleanup chunk file: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"Error streaming chunks: {str(e)}")
            raise StreamingError(f"Streaming failed: {str(e)}")
            
    def process_parallel(
        self,
        process_func,
        max_workers: Optional[int] = None,
        progress_callback=None
    ) -> List[Dict]:
        """
        Process chunks in parallel.
        
        Args:
            process_func: Function to process each chunk
            max_workers: Maximum number of parallel workers
            progress_callback: Optional callback for progress updates
            
        Returns:
            List[Dict]: Results from processing each chunk
        """
        try:
            results = []
            max_workers = max_workers or min(MAX_PARALLEL_CHUNKS, self.total_chunks)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                for chunk in self.stream_chunks():
                    if self._stop_flag:
                        break
                        
                    future = executor.submit(process_func, chunk)
                    futures.append(future)
                    
                for i, future in enumerate(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if progress_callback:
                            progress = ((i + 1) / len(futures)) * 100
                            progress_callback(progress)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing chunk: {str(e)}")
                        results.append({'error': str(e)})
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Error in parallel processing: {str(e)}")
            raise StreamingError(f"Parallel processing failed: {str(e)}")
            
    def stop(self):
        """Stop streaming."""
        self._stop_flag = True
        if self.ffmpeg:
            self.ffmpeg.stop()

class StreamBuffer:
    """Buffer for efficient streaming of large files."""
    
    def __init__(self, file_obj: BinaryIO, buffer_size: int = STREAM_BUFFER_SIZE):
        """
        Initialize stream buffer.
        
        Args:
            file_obj: File object to buffer
            buffer_size: Size of buffer in bytes
        """
        self.file_obj = file_obj
        self.buffer_size = buffer_size
        self.buffer = bytearray(buffer_size)
        self.buffer_pos = 0
        self.buffer_len = 0
        
    def read(self, size: int) -> bytes:
        """
        Read bytes from buffer.
        
        Args:
            size: Number of bytes to read
            
        Returns:
            bytes: Read data
        """
        result = bytearray(size)
        result_pos = 0
        
        while result_pos < size:
            if self.buffer_pos >= self.buffer_len:
                self.buffer_len = self.file_obj.readinto(self.buffer)
                self.buffer_pos = 0
                if self.buffer_len == 0:
                    break
                    
            copy_size = min(
                size - result_pos,
                self.buffer_len - self.buffer_pos
            )
            result[result_pos:result_pos + copy_size] = \
                self.buffer[self.buffer_pos:self.buffer_pos + copy_size]
                
            result_pos += copy_size
            self.buffer_pos += copy_size
            
        return bytes(result[:result_pos])
        
    def seek(self, offset: int, whence: int = os.SEEK_SET):
        """
        Seek to position in file.
        
        Args:
            offset: Offset in bytes
            whence: Seek mode (os.SEEK_SET, os.SEEK_CUR, os.SEEK_END)
        """
        self.file_obj.seek(offset, whence)
        self.buffer_pos = 0
        self.buffer_len = 0
