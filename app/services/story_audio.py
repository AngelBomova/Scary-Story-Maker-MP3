import re
import subprocess
from pathlib import Path
from uuid import uuid4

import imageio_ffmpeg
from openai import OpenAI

from app.config import Settings
from app.schemas import GenerateRequest


LENGTH_GUIDE = {
    "short": "700 to 900 words",
    "medium": "1000 to 1,500 words",
    "long": "1,600 to 2,300 words",
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


BASE_DIR = Path(__file__).resolve().parents[2]
AMBIENCE_DIR = BASE_DIR / "ambience"

AMBIENCE_FILES = {
    "rain": "rain.mp3",
    "stormy-rain": "stormy-rain.mp3",
    "campfire": "campfire.mp3",
    "urban-scare": "urban-scare.mp3",
    "woods-night": "woods-night.mp3",
    "old-house": "old-house.mp3",
}

MAX_TOPIC_CHARS = 1200
MAX_TTS_CHARS = 1600


def require_openai_key(settings: Settings) -> None:
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is empty. Add it to your .env file.")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:50] or "scary-story"


def build_story_prompt(request: GenerateRequest) -> str:
    length = LENGTH_GUIDE[request.length.value]
    ambience = AMBIENCE_GUIDE.get(request.ambience, AMBIENCE_GUIDE["none"])
    topic = request.topic.strip()
    if len(topic) > MAX_TOPIC_CHARS:
        topic = topic[:MAX_TOPIC_CHARS].rsplit(" ", 1)[0]
    return (
        "Write an original scary story for spoken narration.\n"
        f"Topic: {topic}\n"
        f"Target length: {length}\n"
        f"Background mood: {ambience}\n\n"
        "Use calm, believable pacing like a polished true-scary-story channel: realistic setup, slow dread, "
        "plainspoken narration, clear paragraphs, and a lingering ending. Do not imitate any creator's exact wording, "
        "catchphrases, structure, or stories. Avoid graphic sexual content, hateful content, real-person defamation, "
        "or instructions for harm. Return only the story with a short title on the first line."
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


def split_narration_text(text: str, max_chars: int = MAX_TTS_CHARS) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        sentence_buffer = ""
        for sentence in sentences:
            candidate = sentence if not sentence_buffer else f"{sentence_buffer} {sentence}"
            if len(candidate) <= max_chars:
                sentence_buffer = candidate
                continue

            if sentence_buffer:
                chunks.append(sentence_buffer)
            sentence_buffer = sentence

        if sentence_buffer:
            if len(sentence_buffer) <= max_chars:
                current = sentence_buffer
            else:
                for start in range(0, len(sentence_buffer), max_chars):
                    chunks.append(sentence_buffer[start : start + max_chars])

    if current:
        chunks.append(current)

    return chunks or [text[:max_chars]]


def render_narration_chunks(settings: Settings, narration_text: str, voice: str, output_file: Path) -> None:
    chunks = split_narration_text(narration_text)
    if len(chunks) == 1:
        generate_openai_mp3(settings, chunks[0], voice, output_file)
        return

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    temp_files: list[Path] = []
    temp_output = output_file.with_name(f"{output_file.stem}-joined.mp3")
    concat_file = output_file.with_name(f"{output_file.stem}-concat.txt")

    try:
        for index, chunk in enumerate(chunks):
            chunk_file = output_file.with_name(f"{output_file.stem}-part-{index:03d}.mp3")
            generate_openai_mp3(settings, chunk, voice, chunk_file)
            temp_files.append(chunk_file)

        concat_file.write_text(
            "\n".join(f"file '{path.as_posix()}'" for path in temp_files),
            encoding="utf-8",
        )

        command = [
            ffmpeg_exe,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(temp_output),
        ]

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Audio concat failed: {result.stderr.strip()}")

        temp_output.replace(output_file)
    finally:
        for path in temp_files:
            path.unlink(missing_ok=True)
        concat_file.unlink(missing_ok=True)
        temp_output.unlink(missing_ok=True)


def mix_ambience(narration_file: Path, request: GenerateRequest) -> Path:
    if request.ambience == "none" or request.ambience_volume <= 0:
        return narration_file

    ambience_name = AMBIENCE_FILES.get(request.ambience)
    if not ambience_name:
        return narration_file

    ambience_file = AMBIENCE_DIR / ambience_name
    if not ambience_file.exists():
        raise ValueError(
            f"Missing ambience file: {ambience_file}. Add {ambience_name} to the ambience folder."
        )

    mixed_file = narration_file.with_name(f"{narration_file.stem}-mixed.mp3")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    background_volume = max(0, min(request.ambience_volume, 100)) / 100

    command = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(narration_file),
        "-stream_loop",
        "-1",
        "-i",
        str(ambience_file),
        "-filter_complex",
        f"[1:a]volume={background_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(mixed_file),
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Audio mix failed: {result.stderr.strip()}")

    narration_file.unlink(missing_ok=True)
    mixed_file.replace(narration_file)
    return narration_file


def create_story_mp3(settings: Settings, request: GenerateRequest) -> dict[str, str]:
    title, story = generate_story(settings, request)
    settings.output_path.mkdir(parents=True, exist_ok=True)

    filename = f"{slugify(title)}-{uuid4().hex[:8]}.mp3"
    output_file = settings.output_path / filename

    narration_text = f"{title}.\n\n{story}"
    render_narration_chunks(settings, narration_text, request.voice, output_file)
    mix_ambience(output_file, request)

    return {
        "title": title,
        "story": story,
        "filename": filename,
        "audio_url": f"/audio/{filename}",
    }
