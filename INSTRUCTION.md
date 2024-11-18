# AutoLife Media Tools - AI Assistant Instructions

## Project Overview
AutoLife Media Tools is a Python-based application for video subtitle generation and management. The application uses PyQt5 for its GUI and follows a modular architecture.

## Critical Startup Checks
Before processing any user request, ALWAYS verify:

1. Test Files Loading
```python
# Core Logic for Test Files Loading
- Check if test_files directory exists in project root
- Verify test files are loaded in FileListWidget
- Ensure file paths are stored correctly (full path in data, filename in display)
- Confirm supported file formats (.mp4, .wav, .srt) are recognized
```

## Core Functions and Their Logic

### 1. Generate Subtitles
```python
# Core Logic Flow
1. Input Validation
   - Verify input file exists
   - Check if file is video (.mp4, .avi, etc.) or audio (.wav, .mp3, etc.)
   - Ensure HuggingFace API token is available
   - Validate file size against API limits

2. Audio Processing
   - If input is video, extract audio using cloud service if available
   - Convert audio to API-required format (wav/mp3)
   - Consider cloud-based audio preprocessing:
     * Noise reduction
     * Volume normalization
     * Audio quality enhancement

3. Transcription (Cloud-Based)
   - Primary: Use Hugging Face Inference API
     * Automatic language detection
     * High-accuracy transcription
     * Built-in timestamp generation
   - Fallback Options:
     * OpenAI Whisper API
     * Google Speech-to-Text
     * Azure Speech Services
   - Handle API-specific:
     * Rate limits
     * Quota management
     * Error responses
     * Retry logic

4. Post-Processing
   - Use cloud services for:
     * Text formatting
     * Language correction
     * Translation if needed
   - Local processing only for:
     * SRT file formatting
     * Final file saving

5. Output Generation
   - Create SRT file with same name as input
   - Format timestamps correctly (00:00:00,000)
   - Save in same directory as input file
   - Optional: Cache API responses for future use
```

### 2. Convert SRT to ASS
```python
# Core Logic Flow
1. Input Validation
   - Verify input file exists and is .srt format
   - Check SRT file structure (timestamps, text)

2. Style Processing
   - Apply default ASS styles if no template
   - Handle font settings and positioning
   - Process any special formatting

3. Conversion
   - Parse SRT timestamps and text
   - Convert timestamps to ASS format
   - Apply styling to each subtitle line
   - Generate ASS header with style definitions

4. Output Generation
   - Create ASS file with same name as input
   - Ensure all style information is included
   - Maintain subtitle timing accuracy
```

## Error Handling Priority
When encountering errors, check in this order:

1. File System Issues
   - Test files directory existence
   - File permissions
   - File format validation

2. API Issues (for subtitle generation)
   - API token validation
   - API response handling
   - Network connectivity

3. Processing Issues
   - Audio extraction
   - Transcription quality
   - Format conversion accuracy

## UI State Management
Important UI elements to monitor:

1. File List
   - Display: Only filenames
   - Data: Full file paths stored in Qt.UserRole
   - Selection: Multiple files support

2. Progress Tracking
   - Individual file progress
   - Batch processing status
   - Error state display

## Development Guidelines

### AI Service Usage
- Always prefer cloud-based AI services over local processing
- Use Hugging Face's hosted inference API when available
- Consider these services for AI tasks:
  1. Speech-to-Text: Whisper API, Google Speech-to-Text
  2. Translation: Google Translate API, DeepL API
  3. Text Processing: GPT API, Hugging Face Inference API
- Benefits:
  * Reduced local resource usage
  * Better scalability
  * Regular model updates
  * Faster processing
- Implementation:
  * Store API keys in .env file
  * Handle rate limits gracefully
  * Implement proper error handling for API calls
  * Add fallback options for API failures

### Code Organization
- Keep core logic separate from UI
- Use worker threads for heavy processing
- Maintain clear error propagation

### Future Modifications
When adding new features:
1. Follow existing module structure
2. Keep core logic independent of UI
3. Add appropriate logging
4. Update this instruction file

### Testing New Features
1. Verify test files loading first
2. Test with various file formats
3. Check error handling
4. Verify UI responsiveness

## Common Issues and Solutions

### Test Files Not Loading
```python
Check:
1. test_files directory path
2. FileListWidget.add_files() implementation
3. File path handling in main_window.py
4. Supported format definitions
```

### Subtitle Generation Fails
```python
Check:
1. API token in .env
2. Audio extraction process
3. Network connectivity
4. Response handling
```

### SRT to ASS Conversion Issues
```python
Check:
1. Input SRT format validity
2. Style template loading
3. Timestamp conversion accuracy
4. Output file permissions
```

## Future Development Notes

### Cloud-First Development
1. Identify tasks that can be offloaded to cloud services
2. Research available APIs for new features
3. Compare API pricing and rate limits
4. Implement proper API response caching
5. Add offline fallback where necessary

### Adding New Core Functions
1. Define core logic first
2. Implement in separate worker class
3. Add to UI following existing patterns
4. Update this instruction file

### Modifying Existing Functions
1. Preserve core logic flow
2. Update relevant error handling
3. Maintain UI responsiveness
4. Test with existing test files

## Reference for Bug Fixing
When fixing major bugs:
1. Refer to this file's core logic flows
2. Check all critical startup conditions
3. Follow error handling priority
4. Verify UI state management

Remember: Core functionality must work with test files before handling user files.
