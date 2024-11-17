"""
Worker thread for subtitle generation and processing.
"""

import re
import warnings
import torch
import requests
import subprocess
import os
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Union
from PyQt5.QtCore import QThread
from .worker_signals import WorkerSignals
from ..utilities import setup_logger, segment_text
from ..network_utils import APISession, RetryableError, NonRetryableError
from ..streaming_utils import AudioStreamer, StreamingError
from ..constants import (
    API_URL, API_TOKEN, MAX_CHARS_PER_LINE,
    MIN_DURATION, MAX_DURATION, CHARS_PER_SECOND,
    MAX_CHUNK_SIZE, MAX_RETRIES, REQUEST_TIMEOUT,
    MAX_CHUNK_DURATION, MIN_WORDS_PER_LINE, MIN_CHARS_PER_LINE,
    MAX_LINES_PER_SUBTITLE, SENTENCE_END_CHARS, CLAUSE_END_CHARS,
    PUNCTUATION_PAUSE, MIN_LINE_DURATION, MAX_MEMORY_PERCENT,
    MAX_CONCURRENT_TASKS, MEMORY_CHECK_INTERVAL
)
from ..cache_utils import Cache
from ..language_utils import TranslationManager, LanguageError

# Suppress FP16 warning for Whisper
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

class SubtitleWorker(QThread):
    """Worker thread for generating and processing subtitles."""
    
    # Class-level resource management
    _task_semaphore = threading.Semaphore(MAX_CONCURRENT_TASKS)
    _memory_lock = threading.Lock()
    _active_tasks = 0
    
    def __init__(self, files: List[str], batch_size: int = 3):
        """
        Initialize the subtitle worker.
        
        Args:
            files: List of audio files to process
            batch_size: Number of files to process concurrently
        """
        super().__init__()
        self.files = files
        self.batch_size = min(batch_size, MAX_CONCURRENT_TASKS)
        self.signals = WorkerSignals()
        self.logger = setup_logger('SubtitleWorker')
        self.api_session = APISession()
        self.process = psutil.Process(os.getpid())
        self._stop_flag = False
        self.translation_manager = TranslationManager()
        self.logger.info("SubtitleWorker initialized")
        
    def check_memory_usage(self) -> bool:
        """
        Check if memory usage is within acceptable limits.
        
        Returns:
            bool: True if memory usage is acceptable, False otherwise
        """
        try:
            with self._memory_lock:
                memory_percent = self.process.memory_percent()
                if memory_percent > MAX_MEMORY_PERCENT:
                    self.logger.warning(
                        f"Memory usage too high: {memory_percent:.1f}% > {MAX_MEMORY_PERCENT}%"
                    )
                    return False
                return True
        except Exception as e:
            self.logger.error(f"Error checking memory usage: {str(e)}")
            return True  # Continue on error, but log it
            
    def wait_for_resources(self) -> bool:
        """
        Wait for system resources to become available.
        
        Returns:
            bool: True if resources are available, False if operation should be aborted
        """
        while not self._stop_flag:
            if self.check_memory_usage():
                if self._task_semaphore.acquire(blocking=False):
                    return True
                    
            self.logger.debug("Waiting for resources to become available...")
            time.sleep(MEMORY_CHECK_INTERVAL)
            
        return False
        
    def release_resources(self):
        """Release acquired resources."""
        try:
            self._task_semaphore.release()
        except ValueError:
            self.logger.warning("Attempted to release unacquired semaphore")
            
    def stop(self):
        """Signal the worker to stop processing."""
        self._stop_flag = True

    def check_ffmpeg(self):
        """Check if FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                 capture_output=True, 
                                 text=True)
            return True
        except FileNotFoundError:
            self.logger.error("FFmpeg not found. Please install FFmpeg and add it to PATH.")
            self.signals.error.emit("FFmpeg not found. Please install FFmpeg and add it to PATH.")
            return False

    def extract_audio(self, input_file, start_time=None, duration=None):
        """Extract audio from video/audio file to WAV format with improved preprocessing."""
        try:
            if not self.check_ffmpeg():
                raise Exception("FFmpeg not available")

            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(os.path.dirname(input_file), ".temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Generate output path with timestamp
            timestamp = f"_{start_time}" if start_time is not None else ""
            output_file = os.path.join(
                temp_dir, 
                f"{os.path.splitext(os.path.basename(input_file))[0]}{timestamp}.wav"
            )

            # Improved FFmpeg command with strict format settings for Whisper API
            ffmpeg_command = ['ffmpeg', '-i', input_file]
            
            # Add time parameters if specified
            if start_time is not None:
                ffmpeg_command.extend(['-ss', str(start_time)])
            if duration is not None:
                ffmpeg_command.extend(['-t', str(duration)])
            
            # Add output parameters with strict format settings for Whisper API
            ffmpeg_command.extend([
                '-vn',                # Disable video
                '-acodec', 'pcm_s16le',  # Use PCM 16-bit encoding
                '-ar', '16000',          # Set sample rate to 16kHz (required by Whisper)
                '-ac', '1',              # Convert to mono
                '-f', 'wav',             # Force WAV format
                '-sample_fmt', 's16',    # Use signed 16-bit format
                '-bitexact',             # Ensure exact format
                '-y',                    # Overwrite output file
                output_file
            ])

            self.logger.debug(f"FFmpeg command: {' '.join(ffmpeg_command)}")
            result = subprocess.run(ffmpeg_command, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")

            # Verify the output file
            if not os.path.exists(output_file):
                raise Exception("FFmpeg failed to create output file")

            file_size = os.path.getsize(output_file)
            if file_size == 0:
                raise Exception("FFmpeg created an empty output file")

            # Verify the WAV header
            with open(output_file, 'rb') as f:
                header = f.read(44)  # WAV header is 44 bytes
                if len(header) < 44 or header[:4] != b'RIFF' or header[8:12] != b'WAVE':
                    raise Exception("Invalid WAV header")

            self.logger.info(f"Successfully extracted audio to {output_file} ({file_size/1024/1024:.2f} MB)")
            return output_file

        except Exception as e:
            error_msg = f"Failed to extract audio from {input_file}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def get_video_duration(self, input_file):
        """Get video duration in seconds using FFmpeg."""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                input_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFprobe error: {result.stderr}")
            return float(result.stdout.strip())
        except Exception as e:
            self.logger.error(f"Failed to get video duration: {str(e)}")
            raise

    def _process_audio(self, file_path: str) -> List[Dict]:
        """
        Process audio file using streaming for large files.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            List[Dict]: List of transcription results
        """
        try:
            streamer = AudioStreamer(file_path)
            
            def process_chunk(chunk):
                """Process individual audio chunk."""
                try:
                    chunk_file = chunk.to_file()
                    result = self.transcribe_audio(chunk_file)
                    return {
                        'start_time': chunk.start_time,
                        'duration': chunk.duration,
                        'transcription': result
                    }
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {str(e)}")
                    return {
                        'start_time': chunk.start_time,
                        'duration': chunk.duration,
                        'error': str(e)
                    }
            
            def update_progress(progress):
                """Update progress signal."""
                self.signals.status.emit(f"Processing {os.path.basename(file_path)}... ({progress}%)")
            
            results = streamer.process_parallel(
                process_chunk,
                progress_callback=update_progress
            )
            
            # Merge and sort results
            valid_results = [r for r in results if 'error' not in r]
            valid_results.sort(key=lambda x: x['start_time'])
            
            return valid_results
            
        except StreamingError as e:
            self.logger.error(f"Streaming error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
            raise

    def _get_cached_subtitles(self, file_path: str, cache_params: Optional[Dict] = None) -> Optional[str]:
        """
        Check if subtitles are already cached.
        
        Args:
            file_path: Path to media file
            cache_params: Optional cache parameters
            
        Returns:
            Optional[str]: Path to cached subtitles if available
        """
        cache = Cache()
        return cache.get(file_path, {'type': 'subtitles', **cache_params})
    
    def _cache_subtitles(self, file_path: str, subtitle_path: str, cache_params: Optional[Dict] = None) -> Optional[str]:
        """
        Cache generated subtitles.
        
        Args:
            file_path: Original media file path
            subtitle_path: Path to generated subtitles
            cache_params: Optional cache parameters
            
        Returns:
            Optional[str]: Path to cached subtitles
        """
        cache = Cache()
        return cache.put(file_path, subtitle_path, {'type': 'subtitles', **cache_params})
    
    def _get_cached_audio(self, file_path: str) -> Optional[str]:
        """
        Check if extracted audio is already cached.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Optional[str]: Path to cached audio if available
        """
        cache = Cache()
        return cache.get(file_path, {'type': 'audio'})
    
    def _cache_audio(self, file_path: str, audio_path: str) -> Optional[str]:
        """
        Cache extracted audio.
        
        Args:
            file_path: Original media file path
            audio_path: Path to extracted audio
            
        Returns:
            Optional[str]: Path to cached audio
        """
        cache = Cache()
        return cache.put(file_path, audio_path, {'type': 'audio'})

    def format_subtitles(self, transcription_results: List[Dict]) -> List[Dict]:
        """
        Format transcription results into subtitles with proper formatting.
        
        Args:
            transcription_results: List of transcription results
            
        Returns:
            List[Dict]: Formatted subtitles
        """
        try:
            subtitles = []
            
            for result in transcription_results:
                text = result['transcription'].strip()
                if not text:
                    continue
                
                # Detect language and format text
                language_code, formatted_text = self.translation_manager.detect_and_format(text)
                
                # Get formatter for detected language
                formatter = self.translation_manager.get_formatter(language_code)
                
                # Format into subtitle lines
                subtitle_lines = formatter.format_subtitle(formatted_text)
                
                subtitle = {
                    'start_time': result['start_time'],
                    'duration': result['duration'],
                    'text': '\n'.join(subtitle_lines),
                    'language': language_code
                }
                
                subtitles.append(subtitle)
            
            return subtitles
            
        except Exception as e:
            self.logger.error(f"Error formatting subtitles: {str(e)}")
            raise
    
    def translate_subtitles(
        self,
        subtitles: List[Dict],
        target_language: str
    ) -> List[Dict]:
        """
        Translate subtitles to target language.
        
        Args:
            subtitles: List of subtitle dictionaries
            target_language: Target language code
            
        Returns:
            List[Dict]: Translated subtitles
        """
        try:
            return self.translation_manager.translate_subtitles(
                subtitles,
                target_language
            )
        except Exception as e:
            self.logger.error(f"Error translating subtitles: {str(e)}")
            raise
    
    def process_file(
        self,
        media_file: str,
        target_language: Optional[str] = None
    ) -> Optional[str]:
        """
        Process a single media file to generate subtitles.
        
        Args:
            media_file: Path to media file
            target_language: Optional target language for translation
            
        Returns:
            Optional[str]: Path to generated subtitles
        """
        try:
            self.logger.info(f"Processing {media_file}")
            self.signals.status.emit(f"Processing {os.path.basename(media_file)}...")
            
            # Check resource constraints
            if not self.wait_for_resources():
                self.logger.warning(f"Skipping {media_file} due to resource constraints")
                return None
            
            try:
                # Check for cached subtitles
                cache_params = {'target_language': target_language} if target_language else None
                cached_subtitles = self._get_cached_subtitles(media_file, cache_params)
                if cached_subtitles:
                    self.logger.info(f"Using cached subtitles for {media_file}")
                    return cached_subtitles
                
                # Extract or get cached audio
                audio_path = self._get_cached_audio(media_file)
                if not audio_path:
                    audio_path = self.extract_audio(media_file)
                    if not audio_path:
                        return None
                    # Cache extracted audio
                    cached_audio = self._cache_audio(media_file, audio_path)
                    if cached_audio:
                        audio_path = cached_audio
                
                # Process audio in chunks
                transcription_results = self._process_audio(audio_path)
                if not transcription_results:
                    return None
                
                # Generate and format subtitles
                subtitles = self.format_subtitles(transcription_results)
                
                # Translate if needed
                if target_language:
                    subtitles = self.translate_subtitles(subtitles, target_language)
                
                # Write subtitles
                output_file = os.path.splitext(media_file)[0] + ".srt"
                self.write_subtitles(subtitles, output_file)
                
                # Cache subtitles
                cached_path = self._cache_subtitles(media_file, output_file, cache_params)
                if cached_path:
                    output_file = cached_path
                
                return output_file
                
            finally:
                self.release_resources()
                
        except Exception as e:
            self.logger.error(f"Error processing {media_file}: {str(e)}")
            self.signals.error.emit(str(e))
            return None

    def transcribe_audio(self, audio_file):
        """Transcribe audio using Whisper API with improved error handling."""
        try:
            self.logger.info(f"Starting transcription for {audio_file}")
            self.logger.debug(f"File size: {os.path.getsize(audio_file)/1024/1024:.2f} MB")

            # Verify the audio file format before sending
            verify_command = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,channels,sample_rate,bits_per_sample',
                '-of', 'json',
                audio_file
            ]
            
            verify_result = subprocess.run(verify_command, capture_output=True, text=True)
            if verify_result.returncode == 0:
                self.logger.info(f"Audio format verification: {verify_result.stdout}")
            else:
                raise NonRetryableError(f"Failed to verify audio format: {verify_result.stderr}")

            headers = {
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": "audio/wav"
            }
            
            with open(audio_file, "rb") as f:
                audio_data = f.read()
                self.logger.info(f"Sending {len(audio_data)} bytes to API")
                
                try:
                    response = self.api_session.request(
                        'POST',
                        API_URL,
                        data=audio_data,
                        headers=headers
                    )
                    
                    try:
                        result = response.json()
                        self.logger.debug(f"API Response: {result}")
                        
                        if isinstance(result, dict):
                            if "error" in result:
                                if "Malformed soundfile" in str(result["error"]):
                                    raise NonRetryableError("Audio file format is not compatible with Whisper API")
                                raise RetryableError(f"API Error: {result['error']}")
                            
                            # Handle the new response format
                            if "text" in result:
                                # Convert the simple text response to our expected format
                                text = result["text"].strip()
                                if not text:
                                    raise NonRetryableError("Empty transcription result")
                                    
                                formatted_result = {
                                    "segments": [{
                                        "start": 0,
                                        "end": len(text) / CHARS_PER_SECOND,  # Estimate duration
                                        "text": text
                                    }]
                                }
                                return self.format_subtitles(formatted_result)
                            elif "segments" in result:
                                # The response is already in the expected format
                                return self.format_subtitles(result)
                        
                        raise NonRetryableError("Unexpected API response format")
                        
                    except ValueError as e:
                        error_msg = f"Failed to parse API response: {str(e)}\nResponse: {response.text[:1000]}"
                        self.logger.error(error_msg)
                        raise NonRetryableError(error_msg)
                        
                except (RetryableError, NonRetryableError) as e:
                    self.logger.error(f"API request failed: {str(e)}")
                    raise
                    
        except Exception as e:
            error_msg = f"Transcription failed for {audio_file}: {str(e)}"
            self.logger.error(error_msg)
            if isinstance(e, (RetryableError, NonRetryableError)):
                raise
            raise NonRetryableError(error_msg)

    def write_subtitles(self, subtitles, output_file):
        """Write subtitles to file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(sub['text'] for sub in subtitles))
            self.logger.info(f"Successfully generated subtitles: {output_file}")
        except Exception as e:
            error_msg = f"Failed to write subtitles to {output_file}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def run(self):
        """Main worker thread execution."""
        try:
            if not self.check_ffmpeg():
                self.signals.error.emit("FFmpeg not found. Please install FFmpeg.")
                return
                
            successful_files = []
            failed_files = []
            
            with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                future_to_file = {
                    executor.submit(self.process_file, f): f 
                    for f in self.files
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        result = future.result()
                        if result:
                            successful_files.append(file)
                        else:
                            failed_files.append(file)
                    except Exception as e:
                        self.logger.error(f"Error processing {file}: {str(e)}")
                        failed_files.append(file)
                        
            # Report results
            total = len(self.files)
            success_count = len(successful_files)
            fail_count = len(failed_files)
            
            status_msg = f"Completed: {success_count}/{total} files successful"
            if fail_count > 0:
                status_msg += f", {fail_count} failed"
                
            self.signals.status.emit(status_msg)
            self.signals.finished.emit()
            
        except Exception as e:
            self.logger.error(f"Worker thread error: {str(e)}")
            self.signals.error.emit(str(e))
            
        finally:
            # Ensure all resources are released
            try:
                while self._task_semaphore._value < MAX_CONCURRENT_TASKS:
                    self._task_semaphore.release()
            except Exception as e:
                self.logger.error(f"Error releasing resources: {str(e)}")
