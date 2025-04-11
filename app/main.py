from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles
import os
from typing import Dict

from app.utils import transcribe_audio

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# Mount the static directory
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

    transcript = transcribe_audio(file_path, progress_callback)
    
    # Split the transcript into sentences
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
    
@app.get("/transcribe-progress")
async def get_transcribe_progress(request: Request):
    # Return progress for the most recent transcription
    if transcription_progress:
        latest_file = list(transcription_progress.keys())[-1]
        return JSONResponse(content=transcription_progress[latest_file])
    return JSONResponse(content={"percentage": 0, "status": "No active transcription"})
