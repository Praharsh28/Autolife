"""
Worker thread for subtitle generation and processing.
"""

import os
import tempfile
import logging
from typing import List, Dict
from PyQt5.QtCore import QThread

try:
    from .worker_signals import WorkerSignals
    from ..constants import API_TOKEN, MAX_LINE_LENGTH
    from ..utilities import setup_logger
except ImportError:
    from modules.workers.worker_signals import WorkerSignals
    from modules.constants import API_TOKEN, MAX_LINE_LENGTH
    from modules.utilities import setup_logger

class SubtitleWorker(QThread):
    """Worker thread for generating and processing subtitles."""
    
    def __init__(self, files: List[str], language: str = "en", output_format: str = "srt",
                 word_timing: bool = False, speaker_diarization: bool = False,
                 max_speakers: int = 2, batch_size: int = 1, delete_original: bool = False):
        """
        Initialize the subtitle worker.
        
        Args:
            files: List of video files to process
            language: Target language for subtitles (default: "en")
            output_format: Output subtitle format (default: "srt")
            word_timing: Enable word-level timing (default: False)
            speaker_diarization: Enable speaker diarization (default: False)
            max_speakers: Maximum number of speakers for diarization (default: 2)
            batch_size: Number of files to process in parallel (default: 1)
            delete_original: Whether to delete original files after processing (default: False)
        """
        super().__init__()
        self.files = files
        self.language = language
        self.output_format = output_format
        self.word_timing = word_timing
        self.speaker_diarization = speaker_diarization
        self.max_speakers = max_speakers
        self.batch_size = batch_size
        self.delete_original = delete_original
        self.signals = WorkerSignals()
        self.logger = setup_logger('SubtitleWorker')

    def transcribe_audio(self, audio_file: str) -> Dict:
        """
        Transcribe audio using Whisper API with timestamps.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Dict: Transcription results with timestamps
        """
        try:
            import requests
            
            # Using Whisper-large-v3 with timestamp feature
            API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
            headers = {
                "Authorization": f"Bearer {API_TOKEN}"
            }

            with open(audio_file, "rb") as f:
                data = f.read()

            # Request timestamps and text segmentation from the API
            response = requests.post(
                API_URL, 
                headers=headers, 
                data=data,
                params={
                    "wait_for_model": True,
                    "return_timestamps": True
                }
            )
            result = response.json()
            
            self.logger.info(f"API Response: {result}")
            
            # Process the response into segments
            if isinstance(result, dict) and 'chunks' in result:
                segments = []
                for chunk in result['chunks']:
                    if 'timestamp' in chunk and len(chunk['timestamp']) == 2:
                        segments.append({
                            'text': chunk['text'].strip(),
                            'start': float(chunk['timestamp'][0]),
                            'end': float(chunk['timestamp'][1])
                        })
                return {'segments': segments}
            elif isinstance(result, dict) and 'text' in result:
                # Fallback if no timestamps: create segments based on punctuation
                text = result['text'].strip()
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                segments = []
                avg_duration = 3.0  # Average duration per sentence
                
                for i, sentence in enumerate(sentences):
                    segments.append({
                        'text': sentence + '.',
                        'start': i * avg_duration,
                        'end': (i + 1) * avg_duration
                    })
                return {'segments': segments}
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription error: {str(e)}")
            raise

    def format_subtitles(self, transcription: Dict) -> List[Dict]:
        """
        Format transcription into subtitles with natural line breaks.
        
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
                
                # Split long lines for better readability
                if len(text) > MAX_LINE_LENGTH:
                    words = text.split()
                    lines = []
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + 1 > MAX_LINE_LENGTH:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = len(word)
                        else:
                            current_line.append(word)
                            current_length += len(word) + 1
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    text = '\n'.join(lines)
                
                # Ensure minimum display time
                min_duration = max(len(text.split()) * 0.3, 1.5)  # At least 0.3s per word
                if end_time - start_time < min_duration:
                    end_time = start_time + min_duration
                
                subtitles.append({
                    'text': text,
                    'start': start_time,
                    'end': end_time
                })
            
            return subtitles
            
        except Exception as e:
            self.logger.error(f"Error formatting subtitles: {str(e)}")
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
        """Format seconds to SRT timecode (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def run(self):
        """Run the subtitle generation process."""
        try:
            self.logger.info(f"Starting subtitle generation for {len(self.files)} files with batch size {self.batch_size}")
            
            # Process files in batches
            for i in range(0, len(self.files), self.batch_size):
                batch = self.files[i:i + self.batch_size]
                self.logger.info(f"Processing batch {i//self.batch_size + 1}: {batch}")
                
                for file_path in batch:
                    self.process_file(file_path)
            
            self.logger.info("Subtitle generation completed")
            self.signals.finished.emit()
            
        except Exception as e:
            self.logger.error(f"Error during subtitle generation: {str(e)}")
            self.signals.error.emit(str(e))

    def process_file(self, file_path: str):
        """Process a single file."""
        try:
            self.logger.info(f"Processing file: {file_path}")
            self.signals.status.emit(f"Processing {os.path.basename(file_path)}...")
            
            # Extract audio if needed
            audio_file = self.extract_audio(file_path) if not file_path.endswith('.wav') else file_path
            
            # Generate subtitles
            transcription = self.transcribe_audio(audio_file)
            subtitles = self.format_subtitles(transcription)
            output_file = self.save_subtitles(file_path, subtitles)
            
            self.logger.info(f"Successfully processed {file_path}")
            self.signals.file_completed.emit(file_path, 100)
            self.signals.result.emit({
                'input_file': file_path,
                'output_file': output_file,
                'subtitles': subtitles
            })
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            self.logger.error(error_msg)
            self.signals.error.emit(error_msg)

    def extract_audio(self, file_path: str) -> str:
        """Extract audio from video file."""
        try:
            import ffmpeg
            
            output_file = tempfile.mktemp(suffix='.wav')
            
            # Extract audio using ffmpeg
            stream = ffmpeg.input(file_path)
            stream = ffmpeg.output(stream, output_file, acodec='pcm_s16le', ar='44100', ac=2)
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error extracting audio: {str(e)}")
            raise

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
