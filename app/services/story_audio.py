import re
from pathlib import Path
from uuid import uuid4

import httpx
from openai import OpenAI

from app.config import Settings
from app.schemas import GenerateRequest


LENGTH_GUIDE = {
    "short": "650 to 850 words",
    "medium": "1,100 to 1,500 words",
    "long": "1,800 to 2,400 words",
}


STYLE_GUIDE = {
    "campfire": "classic campfire horror with simple, vivid images and a final chill",
    "analog": "analog horror with strange recordings, missing context, and mounting dread",
    "urban": "urban legend horror told like a story someone swears happened nearby",
    "found-footage": "found-footage horror with timestamps, recovered notes, and uneasy realism",
}


def require_openai_key(settings: Settings) -> None:
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is empty. Add it to your .env file.")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:50] or "scary-story"


def build_story_prompt(request: GenerateRequest) -> str:
    length = LENGTH_GUIDE[request.length.value]
    style = STYLE_GUIDE.get(request.style, STYLE_GUIDE["campfire"])
    return (
        "Write an original scary story for narration.\n"
        f"Topic: {request.topic}\n"
        f"Length: {length}\n"
        f"Style: {style}\n\n"
        "Make it atmospheric, paced for spoken audio, and suitable for a general horror audience. "
        "Avoid graphic sexual content, hateful content, real-person defamation, or instructions for harm. "
        "Return only the story with a short title on the first line."
    )


def generate_story(settings: Settings, request: GenerateRequest) -> tuple[str, str]:
    require_openai_key(settings)
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_text_model,
        messages=[
            {
                "role": "system",
                "content": "You write original horror stories that are paced for spoken narration.",
            },
            {"role": "user", "content": build_story_prompt(request)},
        ],
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise ValueError("The story model returned an empty response.")

    first_line, _, rest = text.partition("\n")
    title = first_line.strip().lstrip("#").strip() or "Scary Story"
    story = rest.strip() if rest.strip() else text
    return title, story


def generate_openai_mp3(settings: Settings, text: str, voice: str, output_file: Path) -> None:
    require_openai_key(settings)
    client = OpenAI(api_key=settings.openai_api_key)
    audio = client.audio.speech.create(
        model=settings.openai_tts_model,
        voice=voice,
        input=text,
        response_format="mp3",
    )
    output_file.write_bytes(audio.content)


def generate_elevenlabs_mp3(settings: Settings, text: str, output_file: Path) -> None:
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        raise ValueError("ElevenLabs is not configured.")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    with httpx.Client(timeout=120) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        output_file.write_bytes(response.content)


def create_story_mp3(settings: Settings, request: GenerateRequest) -> dict[str, str]:
    title, story = generate_story(settings, request)
    settings.output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{slugify(title)}-{uuid4().hex[:8]}.mp3"
    output_file = settings.output_path / filename

    narration_text = f"{title}.\n\n{story}"
    if settings.elevenlabs_api_key and settings.elevenlabs_voice_id:
        generate_elevenlabs_mp3(settings, narration_text, output_file)
    else:
        generate_openai_mp3(settings, narration_text, request.voice, output_file)

    return {
        "title": title,
        "story": story,
        "filename": filename,
        "audio_url": f"/audio/{filename}",
    }
