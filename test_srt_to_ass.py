"""
Test script for SRT to ASS conversion.
"""

from modules.converters.srt_to_ass import SRTToASSConverter

def main():
    # Initialize converter
    converter = SRTToASSConverter()
    
    # Convert test file
    input_file = "test_files/1.srt"
    output_file = converter.convert(input_file)
    print(f"Converted {input_file} to {output_file}")

if __name__ == "__main__":
    main()
