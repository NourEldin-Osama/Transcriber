from src.config import settings
from src.transcriber import transcribe


def main():
    """Main function to run the transcription process."""
    input_files = settings.input.urls_or_paths
    if input_files:
        print("Starting transcription...")
        transcribe()
    else:
        print("No input files or URLs provided.")


if __name__ == "__main__":
    main()
