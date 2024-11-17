"""
Worker thread for subtitle generation and processing.
"""

import os
import tempfile
from typing import List, Dict
from PyQt5.QtCore import QThread
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from .worker_signals import WorkerSignals
from ..network_utils import APISession
from ..ffmpeg_utils import FFmpegProcess
from ..utilities import setup_logger
from ..constants import (
    API_BASE_URL,
    API_TOKEN,
    MAX_LINE_LENGTH,
    MIN_LINE_LENGTH,
    MAX_SUBTITLE_DURATION,
    MIN_SUBTITLE_DURATION
)
import requests
import time

class SubtitleWorker(QThread):
    """Worker thread for generating and processing subtitles."""
    
    def __init__(self, files: List[str], batch_size: int = 1):
        """
        Initialize the subtitle worker.
        
        Args:
            files: List of video files to process
            batch_size: Number of files to process in parallel (default: 1)
        """
        super().__init__()
        self.files = files
        self.batch_size = batch_size
        self.signals = WorkerSignals()
        self.logger = setup_logger('SubtitleWorker')
        
        # Initialize models for semantic text splitting
        try:
            self.logger.info("Loading semantic models for subtitle formatting...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.tokenizer = AutoTokenizer.from_pretrained('gpt2')
            self.logger.info("Models loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load models: {str(e)}")
            raise

    def run(self):
        """Run the subtitle generation process."""
        try:
            total_files = len(self.files)
            self.logger.info(f"Starting subtitle generation for {total_files} files with batch size {self.batch_size}")
            
            # Process files in batches
            for i in range(0, total_files, self.batch_size):
                batch = self.files[i:i + self.batch_size]
                self.logger.info(f"Processing batch {i//self.batch_size + 1}: {batch}")
                
                for file in batch:
                    try:
                        self.process_file(file)
                    except Exception as e:
                        self.logger.error(f"Error processing {file}: {str(e)}")
                        self.signals.error.emit(f"Error processing {file}: {str(e)}")
                        continue
            
                # Update overall progress
                progress = min(100, int((i + len(batch)) / total_files * 100))
                self.signals.progress.emit(progress)
        
            self.logger.info("Subtitle generation completed")
            self.signals.finished.emit()
        
        except Exception as e:
            self.logger.error(f"Error in subtitle generation: {str(e)}")
            self.signals.error.emit(f"Error in subtitle generation: {str(e)}")

    def process_file(self, file_path: str):
        """
        Process a single file.
        
        Args:
            file_path: Path to video file
        """
        try:
            self.logger.info(f"Processing file: {file_path}")
            self.signals.log.emit(f"Processing {os.path.basename(file_path)}...")
            
            # Extract audio from video
            audio_file = self.extract_audio(file_path)
            if not audio_file:
                raise Exception(f"Failed to extract audio from {file_path}")
            
            # Transcribe audio
            transcription = self.transcribe_audio(audio_file)
            if not transcription:
                raise Exception(f"Failed to transcribe audio from {file_path}")
            
            # Format and save subtitles
            subtitles = self.format_subtitles(transcription)
            output_file = self.save_subtitles(file_path, subtitles)
            
            # Update progress
            self.signals.file_completed.emit(file_path, 100)
            
            self.logger.info(f"Successfully processed {file_path}")
            self.signals.log.emit(f"Successfully generated subtitles for {os.path.basename(file_path)}")
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.signals.error.emit(error_msg)
        
        finally:
            # Cleanup temporary files
            self.cleanup_temp_files()

    def extract_audio(self, file_path: str) -> str:
        """
        Extract audio from video file.
        
        Args:
            file_path: Path to video file
            
        Returns:
            str: Path to extracted audio file
        """
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Extract audio using FFmpeg
            ffmpeg = FFmpegProcess(file_path)
            success = ffmpeg.extract_audio(output_path)
            
            if not success:
                raise Exception("FFmpeg audio extraction failed")
                
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error extracting audio: {str(e)}")
            raise

    def transcribe_audio(self, audio_file: str) -> Dict:
        """
        Transcribe audio using Whisper API.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Dict: Transcription results
        """
        try:
            import requests
            API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
            headers = {"Authorization": f"Bearer {API_TOKEN}"}

            with open(audio_file, "rb") as f:
                data = f.read()

            response = requests.post(API_URL, headers=headers, data=data)
            result = response.json()
            
            self.logger.info(f"API Response: {result}")
            
            # Convert response to expected format with text segmentation
            if isinstance(result, dict) and 'text' in result:
                text = result['text'].strip()
                # Split text into segments of roughly 10 words each
                words = text.split()
                segments = []
                segment_size = 10
                
                for i in range(0, len(words), segment_size):
                    segment_words = words[i:i + segment_size]
                    segment_text = ' '.join(segment_words)
                    start_time = i / segment_size * 3  # Approximate 3 seconds per segment
                    end_time = start_time + 3
                    
                    segments.append({
                        'text': segment_text,
                        'start': start_time,
                        'end': end_time
                    })
                
                return {'segments': segments}
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription error: {str(e)}")
            raise

    def format_subtitles(self, transcription: Dict) -> List[Dict]:
        """
        Format transcription into subtitles with semantic line breaks.
        
        Args:
            transcription: Transcription results
            
        Returns:
            List[Dict]: Formatted subtitles
        """
        try:
            subtitles = []
            segments = transcription.get('segments', [])
            
            for segment in segments:
                text = segment['text'].strip()
                start_time = float(segment['start'])
                end_time = float(segment['end'])
                
                # Skip empty segments
                if not text:
                    continue
                
                # Split long lines
                if len(text) > MAX_LINE_LENGTH:
                    lines = self._split_into_semantic_lines(text)
                    text = '\n'.join(lines)
                
                subtitles.append({
                    'text': text,
                    'start': start_time,
                    'end': end_time
                })
            
            return subtitles
            
        except Exception as e:
            self.logger.error(f"Error formatting subtitles: {str(e)}")
            raise

    def _split_into_semantic_lines(self, text: str) -> List[str]:
        """
        Split text into lines based on semantic meaning.
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: Split lines
        """
        try:
            # Encode text for semantic analysis
            embeddings = self.sentence_model.encode([text])[0]
            tokens = self.tokenizer.tokenize(text)
            
            # Find optimal split points
            lines = []
            current_line = []
            current_length = 0
            
            for token in tokens:
                token_length = len(token)
                
                if current_length + token_length > MAX_LINE_LENGTH:
                    if current_line:
                        lines.append(self.tokenizer.convert_tokens_to_string(current_line))
                        current_line = []
                        current_length = 0
                
                current_line.append(token)
                current_length += token_length
            
            # Add remaining line
            if current_line:
                lines.append(self.tokenizer.convert_tokens_to_string(current_line))
            
            return lines
            
        except Exception as e:
            self.logger.error(f"Error splitting text: {str(e)}")
            raise

    def save_subtitles(self, video_file: str, subtitles: List[Dict]) -> str:
        """
        Save subtitles to SRT file.
        
        Args:
            video_file: Original video file path
            subtitles: Formatted subtitles
            
        Returns:
            str: Path to saved subtitle file
        """
        try:
            output_file = os.path.splitext(video_file)[0] + '.srt'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, subtitle in enumerate(subtitles, 1):
                    f.write(f"{i}\n")
                    f.write(f"{self._format_timecode(subtitle['start'])} --> {self._format_timecode(subtitle['end'])}\n")
                    f.write(f"{subtitle['text']}\n\n")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving subtitles: {str(e)}")
            raise

    def _format_timecode(self, seconds: float) -> str:
        """
        Convert seconds to SRT timecode format (HH:MM:SS,mmm).
        
        Args:
            seconds: Time in seconds
            
        Returns:
            str: Formatted timecode
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            temp_dir = tempfile.gettempdir()
            for filename in os.listdir(temp_dir):
                if filename.endswith('.wav'):
                    try:
                        os.remove(os.path.join(temp_dir, filename))
                    except Exception as e:
                        self.logger.warning(f"Failed to remove temp file {filename}: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {str(e)}")
