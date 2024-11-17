# Autolife Media Processing Application - User Guide

## Overview
Autolife is a powerful media processing application that generates, translates, and synchronizes subtitles for your video files. With support for multiple languages and intelligent formatting, it makes subtitle creation and management effortless.

## Features
- Automatic subtitle generation
- Multi-language translation
- Intelligent subtitle synchronization
- Batch processing support
- Real-time preview and editing
- Custom subtitle formatting
- Progress tracking and status updates

## Getting Started

### Installation
1. Ensure you have Python 3.8 or later installed
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install FFmpeg (required for media processing)
4. Launch the application:
   ```bash
   python main.py
   ```

### Basic Usage

1. **Adding Files**
   - Click "Add Files" or drag and drop video files
   - Selected files appear in the file list
   - Each file shows its processing status and progress

2. **Language Selection**
   - Choose source language (auto-detect available)
   - Select target languages for translation
   - Language panel shows available options

3. **Processing Files**
   - Select files to process
   - Click "Start Batch" to begin
   - Monitor progress in the file list
   - Cancel processing anytime with "Cancel" button

4. **Previewing Results**
   - Click a file to preview subtitles
   - View original and translated text side by side
   - Use video preview to check timing
   - Make adjustments as needed

### Advanced Features

1. **Subtitle Editing**
   - Double-click subtitle to edit
   - Adjust timing with slider
   - Format text (style, color, position)
   - Preview changes in real-time

2. **Batch Processing**
   - Process multiple files simultaneously
   - Queue additional files while processing
   - Set different languages per file
   - Monitor all tasks in file list

3. **Subtitle Synchronization**
   - Automatic sync point detection
   - Manual timing adjustment
   - Quality score feedback
   - Apply sync to all translations

4. **Export Options**
   - Multiple subtitle formats
   - Embedded or separate files
   - Custom naming patterns
   - Batch export support

## Tips and Tricks

1. **Optimal Performance**
   - Process similar length videos together
   - Limit concurrent files based on CPU
   - Use SRT format for best compatibility
   - Enable caching for repeated tasks

2. **Quality Improvement**
   - Review auto-detected sync points
   - Adjust timing for long dialogues
   - Check speaker detection accuracy
   - Verify language-specific formatting

3. **Resource Management**
   - Monitor disk space usage
   - Clear cache periodically
   - Close preview for large files
   - Use batch processing efficiently

## Troubleshooting

### Common Issues

1. **Processing Fails**
   - Check video file format
   - Verify FFmpeg installation
   - Ensure sufficient disk space
   - Check network connection

2. **Poor Synchronization**
   - Review source video quality
   - Check for complex audio
   - Adjust sync sensitivity
   - Try manual sync points

3. **Translation Issues**
   - Verify language selection
   - Check API connectivity
   - Review source text quality
   - Try alternative translations

### Error Messages

- "FFmpeg not found": Install or update FFmpeg
- "API unavailable": Check network/credentials
- "Insufficient space": Free up disk space
- "File in use": Close other applications

## Support

For additional help:
- Check the [FAQ](FAQ.md)
- Report issues on GitHub
- Contact support team
- Join user community

## Updates

- Check for updates regularly
- Review changelog
- Backup settings before updating
- Follow upgrade instructions
