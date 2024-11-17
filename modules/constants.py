"""
Constants used throughout the media processing application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
TEMPLATES_DIR = os.path.join(RESOURCES_DIR, 'templates')
DEFAULT_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, 'default_template.ass')

# API Configuration
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
if not API_TOKEN:
    raise ValueError("HUGGINGFACE_API_TOKEN not found. Please set it in your .env file")

# Network Configuration
MAX_RETRIES = 5
BASE_RETRY_DELAY = 1.0  # Initial retry delay in seconds
MAX_RETRY_DELAY = 32.0  # Maximum retry delay in seconds
JITTER_RANGE = 0.1  # ±10% jitter
REQUEST_TIMEOUT = 30  # Request timeout in seconds
RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}  # HTTP status codes that trigger retry

# API Request Limits
MAX_CHUNK_SIZE = 25 * 1024 * 1024  # 25MB in bytes
MAX_CHUNK_DURATION = 300  # 5 minutes in seconds

# Streaming Configuration
CHUNK_SIZE = 1024 * 1024  # 1MB default chunk size
MAX_CHUNK_DURATION = 300  # Maximum chunk duration in seconds (5 minutes)
MIN_CHUNK_SIZE = 512 * 1024  # Minimum chunk size (512KB)
CHUNK_OVERLAP = 1.0  # Overlap between chunks in seconds
MAX_CHUNKS_IN_MEMORY = 10  # Maximum number of chunks to keep in memory
STREAM_BUFFER_SIZE = 8192  # Stream buffer size in bytes (8KB)
MAX_PARALLEL_CHUNKS = 4  # Maximum number of chunks to process in parallel

# Subtitle Configuration
MAX_CHARS_PER_LINE = 42     # Standard for comfortable reading 
MIN_CHARS_PER_LINE = 20     # Reduced to allow more natural breaks
MIN_DURATION = 1.0          # Increased minimum duration for better readability
MAX_DURATION = 7.0          # Reduced maximum duration for better engagement
CHARS_PER_SECOND = 20       # Reduced for more comfortable reading speed
MIN_WORDS_PER_LINE = 3      # Reduced to allow more natural breaks
MAX_LINES_PER_SUBTITLE = 2  # Maximum lines per subtitle block
MIN_LINE_DURATION = 1.0     # Minimum duration for a single line
PUNCTUATION_PAUSE = {
    '.': 0.6,
    '!': 0.6,
    '?': 0.6,
    ',': 0.3,
    ';': 0.4,
    ':': 0.4
}   # Additional pause after punctuation
SENTENCE_END_CHARS = {'.', '!', '?'}   # Characters that end a sentence
CLAUSE_END_CHARS = {',', ';', ':'}     # Characters that end a clause

# Resource Management
MAX_MEMORY_PERCENT = 80.0  # Maximum memory usage as percentage of system memory
MAX_CONCURRENT_TASKS = 3   # Maximum number of concurrent processing tasks
MEMORY_CHECK_INTERVAL = 1.0  # Seconds between memory checks
CLEANUP_DELAY = 5.0  # Seconds to wait before cleaning up temporary files

# Disk Management
MIN_FREE_SPACE_BYTES = 1024 * 1024 * 1024  # 1GB minimum free space
TEMP_DIR_CLEANUP_THRESHOLD = 85.0  # Clean temp files when disk usage exceeds 85%
TEMP_FILE_MAX_AGE = 3600 * 24  # 24 hours maximum temp file age
DISK_CHECK_INTERVAL = 300  # Check disk space every 5 minutes

# Cache Configuration
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
CACHE_MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB maximum cache size
CACHE_MAX_AGE = 7 * 24 * 3600  # 7 days maximum cache age
CACHE_CLEANUP_INTERVAL = 3600  # Cleanup every hour
CACHE_MIN_FREE_SPACE = 1024 * 1024 * 1024  # 1GB minimum free space

# FFmpeg Configuration
FFMPEG_TIMEOUT = 3600  # 1 hour maximum process time
FFMPEG_FORMATS = {
    'wav': 'Waveform Audio',
    'mp3': 'MP3 Audio',
    'aac': 'AAC Audio',
    'flac': 'FLAC Audio',
    'ogg': 'OGG Vorbis'
}
FFMPEG_COMMAND_TEMPLATES = {
    'wav': '-acodec pcm_s16le -ar 16000 -ac 1',  # 16-bit PCM, 16kHz, mono
    'mp3': '-codec:a libmp3lame -qscale:a 2',    # High quality MP3
    'aac': '-codec:a aac -b:a 192k',             # High quality AAC
    'flac': '-codec:a flac',                      # Lossless FLAC
    'ogg': '-codec:a libvorbis -qscale:a 6'      # High quality Vorbis
}

# Window Configuration
WINDOW_TITLE = "AutoLife Media Processor"
WINDOW_GEOMETRY = (100, 100, 1200, 800)  # x, y, width, height
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 30
SPACING = 10
MARGIN = 20

# UI Theme Colors - Modern Dark Theme
DARK_THEME = {
    'background': '#1E1E1E',           # Dark gray background
    'text': '#E8E8E8',                 # Light gray text
    'button': '#2D2D2D',               # Slightly lighter gray for buttons
    'button_text': '#FFFFFF',          # White text for buttons
    'button_hover': '#3D3D3D',         # Lighter gray for button hover
    'highlight': '#0078D4',            # Blue highlight color
    'highlight_text': '#FFFFFF',       # White text for highlighted items
    'error': '#FF3333',                # Red for errors
    'success': '#33CC33',              # Green for success
    'warning': '#FFCC00',              # Yellow for warnings
    'progress_bar': '#0078D4',         # Blue for progress bar
    'group_box': '#252526',            # Slightly different background for group boxes
    'group_box_title': '#E8E8E8',      # Light gray for group box titles
    'list_background': '#252526',      # Background for file list
    'list_alternate': '#2D2D2D',       # Alternate row color
    'list_selected': '#094771',        # Selected item background
    'status_background': '#252526',    # Background for status display
    'status_text': '#E8E8E8',          # Text color for status display
    'border': '#3D3D3D'                # Border color for widgets
}

# File Extensions
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
SUBTITLE_EXTENSIONS = {'.srt', '.vtt', '.sub', '.ass'}

# Progress Updates
PROGRESS_UPDATE_INTERVAL = 100  # Milliseconds between progress updates

# Language Configuration
SUPPORTED_LANGUAGES = {
    "English", "Spanish", "French", "German", "Italian", "Portuguese",
    "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi"
}
DEFAULT_LANGUAGE = "English"

# Subtitle Duration Limits
MIN_LINE_DURATION = 1.0  # Minimum duration for a subtitle line in seconds
MAX_LINE_DURATION = 7.0  # Maximum duration for a subtitle line in seconds

# Language Codes
LANGUAGE_CODES = {
    'eng': 'en', 'spa': 'es', 'fra': 'fr', 'deu': 'de',
    'ita': 'it', 'por': 'pt', 'nld': 'nl', 'pol': 'pl',
    'rus': 'ru', 'ukr': 'uk', 'ara': 'ar', 'hin': 'hi',
    'ben': 'bn', 'zho': 'zh', 'jpn': 'ja', 'kor': 'ko'
}

LANGUAGE_DIRECTIONS = {
    'ar': 'rtl',  # Arabic
    'he': 'rtl',  # Hebrew
    'fa': 'rtl',  # Persian
    'ur': 'rtl'   # Urdu
}

LANGUAGE_MODELS = {
    ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
    ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
    ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
    ('en', 'it'): 'Helsinki-NLP/opus-mt-en-it',
    ('en', 'pt'): 'Helsinki-NLP/opus-mt-en-pt',
    ('en', 'ru'): 'Helsinki-NLP/opus-mt-en-ru',
    ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
    ('en', 'ar'): 'Helsinki-NLP/opus-mt-en-ar',
    'default': 'facebook/m2m100_418M'  # Fallback for unsupported pairs
}

PUNCTUATION_RULES = {
    'en': {
        'patterns': {
            r'\s+': ' ',  # Normalize whitespace
            r'\.{3,}': '...',  # Normalize ellipsis
            r'["\']([^"\']*)["\']': r'"\1"',  # Normalize quotes
            r'\s*([.,!?;:])\s*': r'\1 ',  # Fix punctuation spacing
        }
    },
    'zh': {
        'patterns': {
            r'\s+': '',  # Remove spaces between Chinese characters
            r'\.{3,}': '...',
            r'["\']([^"\']*)["\']': r'「\1」',  # Chinese quotes
            r'([。，！？；：])': r'\1',  # No space after Chinese punctuation
        }
    },
    'ja': {
        'patterns': {
            r'\s+': '',
            r'\.{3,}': '...',
            r'["\']([^"\']*)["\']': r'「\1」',
            r'([。、！？；：])': r'\1',
        }
    },
    'ar': {
        'patterns': {
            r'\s+': ' ',
            r'\.{3,}': '...',
            r'["\']([^"\']*)["\']': r'"\1"',
            r'\s*([.،!؟;:])\s*': r'\1 ',
        }
    }
}

SUBTITLE_RULES = {
    'en': {
        'max_chars_per_line': 42,
        'min_chars_per_line': 20,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 20
    },
    'zh': {
        'max_chars_per_line': 30,  # Chinese characters need more space
        'min_chars_per_line': 15,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 15
    },
    'ja': {
        'max_chars_per_line': 30,
        'min_chars_per_line': 15,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 15
    },
    'ar': {
        'max_chars_per_line': 50,  # Arabic script is more compact
        'min_chars_per_line': 25,
        'max_lines': 2,
        'min_duration': 1.0,
        'max_duration': 7.0,
        'chars_per_second': 25
    }
}

# File size limits
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
MIN_DURATION = 0.1  # seconds
MAX_DURATION = 7200  # 2 hours

# Media formats
SUPPORTED_VIDEO_FORMATS = ['mp4', 'mkv', 'avi', 'mov', 'wmv']
SUPPORTED_AUDIO_FORMATS = ['mp3', 'wav', 'aac', 'm4a', 'flac']
