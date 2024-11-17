"""Media processing functionality for the AutoLife application."""

import os
import logging
import ffmpeg
from typing import List, Dict, Optional
from pathlib import Path

class MediaProcessor:
    """Handles media file processing operations."""
    
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.aac', '.m4a', '.flac'}
    
    def __init__(self):
        self.probe_info = None
        self._initialize_ffmpeg()
    
    def _initialize_ffmpeg(self):
        """Initialize FFmpeg with proper error handling."""
        try:
            import ffmpeg
            self.ffmpeg = ffmpeg
        except ImportError:
            raise ImportError("FFmpeg-python is required. Please install it with: pip install ffmpeg-python")
    
    def _probe_file(self, file_path: str) -> dict:
        """Probe media file for information with proper error handling."""
        if not file_path or not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            self.probe_info = self.ffmpeg.probe(file_path)
            return self.probe_info
        except self.ffmpeg.Error as e:
            raise ValueError(f"FFmpeg error while probing {file_path}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error while probing {file_path}: {str(e)}")
    
    def supported_formats(self) -> dict:
        """Get supported media formats."""
        return {
            'video': sorted(list(self.SUPPORTED_VIDEO_FORMATS)),
            'audio': sorted(list(self.SUPPORTED_AUDIO_FORMATS))
        }
    
    def get_video_info(self, file_path: str) -> dict:
        """Extract video information with enhanced error handling."""
        probe = self._probe_file(file_path)
        
        try:
            video_stream = next(
                stream for stream in probe['streams'] 
                if stream['codec_type'] == 'video'
            )
            
            # Calculate duration properly
            duration = float(probe.get('format', {}).get('duration', 0))
            if duration == 0 and 'duration' in video_stream:
                duration = float(video_stream['duration'])
                
            return {
                'duration': duration,
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name', 'unknown'),
                'bitrate': int(probe.get('format', {}).get('bit_rate', 0))
            }
        except StopIteration:
            raise ValueError(f"No video stream found in {file_path}")
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid video format in {file_path}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error processing video {file_path}: {str(e)}")
    
    def get_audio_info(self, file_path: str) -> dict:
        """Extract audio information with enhanced error handling."""
        probe = self._probe_file(file_path)
        
        try:
            audio_stream = next(
                stream for stream in probe['streams'] 
                if stream['codec_type'] == 'audio'
            )
            
            duration = float(probe.get('format', {}).get('duration', 0))
            if duration == 0 and 'duration' in audio_stream:
                duration = float(audio_stream['duration'])
                
            return {
                'duration': duration,
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bitrate': int(probe.get('format', {}).get('bit_rate', 0))
            }
        except StopIteration:
            raise ValueError(f"No audio stream found in {file_path}")
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid audio format in {file_path}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error processing audio {file_path}: {str(e)}")
            
    def process_file(self, input_path: str, output_path: str, **options) -> bool:
        """Process media file with comprehensive error handling."""
        if not Path(input_path).exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        try:
            stream = self.ffmpeg.input(input_path)
            
            # Apply processing options
            if options.get('video', True):
                stream = self._apply_video_options(stream, options)
            if options.get('audio', True):
                stream = self._apply_audio_options(stream, options)
                
            # Run the processing
            stream = self.ffmpeg.output(stream, output_path)
            self.ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            return True
        except self.ffmpeg.Error as e:
            raise ValueError(f"FFmpeg processing error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during processing: {str(e)}")
            
    def _apply_video_options(self, stream, options: dict):
        """Apply video processing options with validation."""
        if 'resolution' in options:
            width, height = options['resolution']
            if not (isinstance(width, int) and isinstance(height, int)):
                raise ValueError("Resolution must be tuple of integers")
            stream = self.ffmpeg.filter(stream, 'scale', width, height)
            
        if 'fps' in options:
            fps = options['fps']
            if not isinstance(fps, (int, float)) or fps <= 0:
                raise ValueError("FPS must be a positive number")
            stream = self.ffmpeg.filter(stream, 'fps', fps)
            
        return stream
        
    def _apply_audio_options(self, stream, options: dict):
        """Apply audio processing options with validation."""
        if 'sample_rate' in options:
            rate = options['sample_rate']
            if not isinstance(rate, int) or rate <= 0:
                raise ValueError("Sample rate must be a positive integer")
            stream = self.ffmpeg.filter(stream, 'aresample', rate)
            
        if 'channels' in options:
            channels = options['channels']
            if not isinstance(channels, int) or channels <= 0:
                raise ValueError("Channels must be a positive integer")
            stream = self.ffmpeg.filter(stream, 'channelmap', channels)
            
        return stream
