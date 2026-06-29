import re
from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from app.config import Settings
from app.schemas import GenerateRequest


LENGTH_GUIDE = {
    "short": "650 to 850 words",
    "medium": "1,100 to 1,500 words",
    "long": "1,800 to 2,400 words",
}


AMBIENCE_GUIDE = {
    "none": "no specific background ambience",
    "rain": "steady rain against windows and pavement",
    "stormy-rain": "stormy rain with distant thunder and sudden gusts",
    "campfire": "a low campfire in dark woods, with quiet crackles and long silences",
    "urban-scare": "a late-night city atmosphere with empty streets, distant traffic, and uneasy apartments",
    "woods-night": "woods at night with insects, branches, far-off movement, and deep quiet",
    "old-house": "an old house with floorboards, vents, pipes, and rooms that feel occupied",
}


def require_openai_key(settings: Settings) -> None:
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is empty. Add it to your .env file.")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:50] or "scary-story"


def build_story_prompt(request: GenerateRequest) -> str:
    length = LENGTH_GUIDE[request.length.value]
    ambience = AMBIENCE_GUIDE.get(request.ambience, AMBIENCE_GUIDE["none"])
    return (
        "Write an original scary story for narration.\n"
        f"Topic: {request.topic}\n"
        f"Length: {length}\n"
        f"Background ambience to imagine while writing: {ambience}\n\n"
        "Aim for the calm, believable pacing of popular true-scary-story narration channels: "
        "plainspoken first-person or close third-person narration, realistic setup, slow escalation, "
        "specific ordinary details, short moments of silence implied by paragraph breaks, and a final image "
        "that lingers. Do not copy any creator's exact wording, catchphrases, structure, or stories.\n\n"
        "Make every paragraph easy to read aloud. Build dread gradually before the reveal. "
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


def create_story_mp3(settings: Settings, request: GenerateRequest) -> dict[str, str]:
    title, story = generate_story(settings, request)
    settings.output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{slugify(title)}-{uuid4().hex[:8]}.mp3"
    output_file = settings.output_path / filename

    narration_text = f"{title}.\n\n{story}"
    generate_openai_mp3(settings, narration_text, request.voice, output_file)

    return {
        "title": title,
        "story": story,
        "filename": filename,
        "audio_url": f"/audio/{filename}",
    }
