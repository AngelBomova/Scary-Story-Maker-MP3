from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.schemas import GenerateRequest, GenerateResponse
from app.services.story_audio import create_story_mp3


app = FastAPI(title="Scary Story MP3 Maker")

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/generate", response_model=GenerateResponse)
def generate(
    request: GenerateRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    try:
        return create_story_mp3(settings, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc


@app.get("/audio/{filename}")
def audio(filename: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    audio_file = settings.output_path / filename
    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(audio_file, media_type="audio/mpeg", filename=filename)
