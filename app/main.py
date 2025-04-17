from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pytubefix import YouTube
from typing import Dict
from app.utils import transcribe_audio
import re
import os
import aiofiles

YOUTUBE_REGEX = re.compile(
    r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store transcription progress
transcription_progress: Dict[str, dict] = {}

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_audio(request: Request, file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    transcription_progress[file.filename] = {
        "percentage": 0,
        "status": "Starting transcription..."
    }

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    def progress_callback(percentage: int, status: str):
        transcription_progress[file.filename] = {
            "percentage": percentage,
            "status": status
        }

    # Start transcription
    transcript = transcribe_audio(file_path, progress_callback)
    
    # Format transcript by splitting into sentences and removing extra spaces
    formatted_transcript = '. '.join(
        sent.strip() 
        for sent in transcript.split('.') 
        if sent.strip()
    )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "transcript": formatted_transcript,
            "filename": file.filename
        }
    )

@app.post("/transcribe-url", response_class=HTMLResponse)
async def transcribe_url(request: Request, youtube_url: str = Form(...)):
    if not YOUTUBE_REGEX.match(youtube_url):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "transcript": "❌ Invalid YouTube URL format."
        })

    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True).first()

        if not stream:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "transcript": "❌ No audio stream found."
            })

        audio_filename = f"{yt.video_id}.mp4"
        audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)

        if not os.path.exists(audio_path):
            stream.download(output_path=UPLOAD_FOLDER, filename=audio_filename)

        result = transcribe_audio(audio_path)
        os.remove(audio_path)

        return templates.TemplateResponse("result.html", {
            "request": request,
            "transcript": result,
            "filename": audio_filename
        })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "transcript": f"⚠️ Error: {str(e)}"
        })

@app.get("/transcribe-progress")
async def get_transcribe_progress(request: Request):
    # Return progress for the most recent transcription
    if transcription_progress:
        latest_file = list(transcription_progress.keys())[-1]
        return JSONResponse(content=transcription_progress[latest_file])
    return JSONResponse(content={"percentage": 0, "status": "No active transcription"})
