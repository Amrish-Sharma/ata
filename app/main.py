from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pytubefix import YouTube
from app.utils import transcribe_audio
from datetime import datetime
import logging,aiofiles,os,re

# Configure logging
log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

YOUTUBE_REGEX = re.compile(
    r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    logger.info(f"Access to upload form from {request.client.host}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_audio(request: Request, file: UploadFile = File(...)):
    logger.info(f"File upload started: {file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Start transcription
        logger.info(f"Starting transcription for {file.filename}")
        transcript = transcribe_audio(file_path)
        logger.info(f"Transcription completed for {file.filename}")

        
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
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise

@app.post("/transcribe-url", response_class=HTMLResponse)
async def transcribe_url(request: Request, youtube_url: str = Form(...)):
    logger.info(f"YouTube URL transcription request: {youtube_url}")
    
    if not YOUTUBE_REGEX.match(youtube_url):
        logger.warning(f"Invalid YouTube URL format: {youtube_url}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "transcript": "❌ Invalid YouTube URL format."
        })

    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True).first()

        if not stream:
            logger.warning(f"No audio stream found for URL: {youtube_url}")
            return templates.TemplateResponse("index.html", {
                "request": request,
                "transcript": "❌ No audio stream found."
            })

        audio_filename = f"{yt.video_id}.mp4"
        audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)

        if not os.path.exists(audio_path):
            logger.info(f"Downloading audio from YouTube: {yt.title}")
            stream.download(output_path=UPLOAD_FOLDER, filename=audio_filename)

        logger.info(f"Starting transcription for YouTube video: {yt.title}")
        result = transcribe_audio(audio_path)
        logger.info(f"Transcription completed for YouTube video: {yt.title}")
        os.remove(audio_path)
        logger.info(f"Cleaned up temporary file: {audio_path}")


        return templates.TemplateResponse("result.html", {
            "request": request,
            "transcript": result,
            "filename": audio_filename
        })

    except Exception as e:
        logger.error(f"Error processing YouTube URL {youtube_url}: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "transcript": f"⚠️ Error: {str(e)}"
        })