import whisper

model = whisper.load_model("base")

def transcribe_audio(file_path: str, progress_callback=None):
    try:
        result = model.transcribe(file_path)
        return result['text']
    
    except Exception as e:
        if progress_callback:
            progress_callback(100, f"Error: {str(e)}")
        return f"Error during transcription: {str(e)}"
