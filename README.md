# Transcriber

A flexible Python package for transcribing audio and video from various sources (SoundCloud, YouTube, or local files) into multiple text formats (txt, docx, srt). The transcriber supports multiple speech recognition models (defaulting to Whisper "large-v3"). It leverages GPU acceleration for faster processing and utilizes concurrency through async and multiprocessing to improve performance.

## Features

- **Multiple Input Sources**: Transcribe from SoundCloud, YouTube, or local audio/video files.
- **Multiple Models**: Easily switch between different speech recognition models.
- **GPU Acceleration**: Utilize GPU processing for faster transcription.
- **Concurrent Processing**: Implement async and multiprocessing for improved performance.
- **Various Output Formats**: Export transcriptions to txt, docx, or srt formats.

## Installation

Install the required packages:

```bash
uv pip install -r requirements.txt
```

## Usage

Provide examples on how to use the package:

```python
# Example command to transcribe a YouTube video
import transcriber

transcriber.transcrib(
    source="youtube",
    url="https://www.youtube.com/watch?v=6Jv8GKZlX2A",
    model="whisper-large-v3",
    output_format= ["txt", "docx", "srt"],
    output_dir="output"
)
```

## Contributing

Contributions are welcome. Please submit a pull request or open an issue for suggestions.
