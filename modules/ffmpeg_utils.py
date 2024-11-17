"""
FFmpeg utilities for audio/video processing with improved error handling and monitoring.
"""

import os
import time
import signal
import subprocess
import threading
from typing import Optional, Dict, List, Tuple, Union
from pathlib import Path
from .utilities import setup_logger
from .disk_utils import check_disk_space, estimate_space_needed
from .constants import (
    FFMPEG_TIMEOUT, FFMPEG_FORMATS, MAX_RETRIES,
    MIN_FREE_SPACE_BYTES, FFMPEG_COMMAND_TEMPLATES
)

logger = setup_logger('ffmpeg_utils')

class FFmpegError(Exception):
    """Base exception for FFmpeg-related errors."""
    pass

class FFmpegNotFoundError(FFmpegError):
    """Exception raised when FFmpeg is not installed or not accessible."""
    pass

class FFmpegProcessError(FFmpegError):
    """Exception raised when FFmpeg process fails."""
    def __init__(self, message: str, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr

class FFmpegTimeoutError(FFmpegError):
    """Exception raised when FFmpeg process times out."""
    pass

def check_ffmpeg() -> bool:
    """
    Check if FFmpeg is installed and accessible.
    
    Returns:
        bool: True if FFmpeg is available, False otherwise
        
    Raises:
        FFmpegNotFoundError: If FFmpeg is not found
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise FFmpegNotFoundError("FFmpeg is installed but not working properly")
        return True
    except subprocess.TimeoutExpired:
        raise FFmpegNotFoundError("FFmpeg check timed out")
    except FileNotFoundError:
        raise FFmpegNotFoundError("FFmpeg is not installed")
    except Exception as e:
        raise FFmpegNotFoundError(f"FFmpeg check failed: {str(e)}")

class FFmpegProcess:
    """Class to manage FFmpeg process execution with monitoring."""
    
    def __init__(self, input_file: str):
        """
        Initialize FFmpeg process manager.
        
        Args:
            input_file: Path to input file
        """
        self.input_file = input_file
        self.process: Optional[subprocess.Popen] = None
        self.start_time: float = 0
        self.duration: Optional[float] = None
        self._stop_flag = False
        self._progress_thread: Optional[threading.Thread] = None
        self.logger = setup_logger(f'FFmpegProcess_{os.path.basename(input_file)}')
        
    def _monitor_progress(self, callback=None):
        """Monitor FFmpeg progress and optionally call callback function."""
        while self.process and not self._stop_flag:
            try:
                if self.process.poll() is not None:
                    break
                    
                if callback and self.duration:
                    elapsed = time.time() - self.start_time
                    progress = min(100, (elapsed / self.duration) * 100)
                    callback(progress)
                    
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error monitoring progress: {str(e)}")
                break
                
    def get_duration(self) -> Optional[float]:
        """Get media file duration using FFprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.input_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
                
        except Exception as e:
            self.logger.error(f"Error getting duration: {str(e)}")
            
        return None
        
    def run(
        self,
        output_file: str,
        options: List[str],
        timeout: Optional[int] = None,
        progress_callback=None
    ) -> bool:
        """
        Run FFmpeg process with monitoring.
        
        Args:
            output_file: Path to output file
            options: FFmpeg command options
            timeout: Process timeout in seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            FFmpegProcessError: If process fails
            FFmpegTimeoutError: If process times out
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Check disk space before running
            space_needed = estimate_space_needed(self.input_file)
            if not check_disk_space(output_dir or '.', space_needed):
                raise FFmpegProcessError(
                    f"Insufficient disk space. Need {space_needed/1024/1024:.1f}MB"
                )
                
            # Get input duration
            self.duration = self.get_duration()
            
            # Prepare command
            cmd = ['ffmpeg', '-i', self.input_file] + options + [output_file]
            
            self.logger.info(f"Starting FFmpeg: {' '.join(cmd)}")
            self.start_time = time.time()
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Start progress monitoring
            if progress_callback:
                self._progress_thread = threading.Thread(
                    target=self._monitor_progress,
                    args=(progress_callback,)
                )
                self._progress_thread.start()
                
            # Wait for completion
            try:
                stdout, stderr = self.process.communicate(timeout=timeout or FFMPEG_TIMEOUT)
                
                if self.process.returncode != 0:
                    raise FFmpegProcessError(
                        f"FFmpeg failed with code {self.process.returncode}",
                        stdout=stdout,
                        stderr=stderr
                    )
                    
                # Verify file was created
                if not os.path.exists(output_file):
                    raise FFmpegProcessError(f"Output file was not created: {output_file}")
                    
                if os.path.getsize(output_file) == 0:
                    raise FFmpegProcessError(f"Output file is empty: {output_file}")
                    
                # Add small delay to ensure file is fully written
                time.sleep(0.1)
                
                return True
                
            except subprocess.TimeoutExpired:
                self.stop()
                raise FFmpegTimeoutError(
                    f"FFmpeg process timed out after {timeout or FFMPEG_TIMEOUT} seconds"
                )
                
        except Exception as e:
            if not isinstance(e, (FFmpegProcessError, FFmpegTimeoutError)):
                raise FFmpegProcessError(str(e))
            raise
            
        finally:
            self._stop_flag = True
            if self._progress_thread and self._progress_thread.is_alive():
                self._progress_thread.join()
                
    def stop(self):
        """Stop the FFmpeg process."""
        self._stop_flag = True
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception as e:
                self.logger.error(f"Error stopping FFmpeg process: {str(e)}")
                
    def extract_audio_chunk(
        self,
        output_file: str,
        start_time: float,
        duration: float,
        progress_callback=None
    ) -> bool:
        """
        Extract a chunk of audio from file.
        
        Args:
            output_file: Path to output file
            start_time: Start time in seconds
            duration: Duration in seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            options = [
                '-ss', str(start_time),
                '-t', str(duration),
                '-vn',  # Disable video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y'  # Overwrite output file
            ]
            
            return self.run(output_file, options, progress_callback=progress_callback)
            
        except Exception as e:
            self.logger.error(f"Error extracting audio chunk: {str(e)}")
            return False

    def extract_audio(self, output_file: str, progress_callback=None) -> bool:
        """
        Extract audio from video file.
        
        Args:
            output_file: Path to output WAV file
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Check disk space
            space_needed = estimate_space_needed(self.input_file)
            if not check_disk_space(os.path.dirname(output_file), space_needed):
                raise FFmpegError(f"Insufficient disk space. Need at least {space_needed/1024/1024:.2f} MB")
            
            # Setup FFmpeg options for audio extraction
            options = [
                "-y",                   # Overwrite output file
                "-i", self.input_file,  # Input file
                "-vn",                  # Disable video
                "-acodec", "pcm_s16le", # Audio codec (16-bit PCM)
                "-ar", "44100",         # Sample rate (44.1 kHz)
                "-ac", "2",             # Stereo audio
                output_file             # Output file
            ]
            
            # Run FFmpeg
            return self.run(output_file, options, progress_callback=progress_callback)
            
        except Exception as e:
            self.logger.error(f"Error extracting audio: {str(e)}")
            raise FFmpegError(f"Error extracting audio: {str(e)}")

def convert_audio(
    input_file: str,
    output_file: str,
    format: str = "wav",
    progress_callback=None
) -> bool:
    """
    Convert audio file to specified format.
    
    Args:
        input_file: Path to input file
        output_file: Path to output file
        format: Output format (default: wav)
        progress_callback: Optional callback for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if format not in FFMPEG_FORMATS:
            raise ValueError(f"Unsupported format: {format}")
            
        template = FFMPEG_COMMAND_TEMPLATES.get(format, FFMPEG_COMMAND_TEMPLATES['wav'])
        options = template.split()
        
        ffmpeg = FFmpegProcess(input_file)
        return ffmpeg.run(output_file, options, progress_callback=progress_callback)
        
    except Exception as e:
        logger.error(f"Error converting audio: {str(e)}")
        return False

def extract_audio_chunk(
    input_file: str,
    output_file: str,
    start_time: float,
    duration: float,
    progress_callback=None
) -> bool:
    """
    Extract a chunk of audio from file.
    
    Args:
        input_file: Path to input file
        output_file: Path to output file
        start_time: Start time in seconds
        duration: Duration in seconds
        progress_callback: Optional callback for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ffmpeg = FFmpegProcess(input_file)
        return ffmpeg.extract_audio_chunk(output_file, start_time, duration, progress_callback=progress_callback)
        
    except Exception as e:
        logger.error(f"Error extracting audio chunk: {str(e)}")
        return False
