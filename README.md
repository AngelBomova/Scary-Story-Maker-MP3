# Scary Story MP3 Maker

A local web app that writes a scary story from a prompt, turns it into an MP3, and gives you a playable/downloadable audio file.

## What You Need

1. Python installed on your computer.
2. An OpenAI API key in `.env`.
3. The ambience MP3 files already placed in the `ambience` folder.

## Run It

1. Open PowerShell in this folder:

```text
C:\Users\Angel\Desktop\Coding Projects\Scary Story Maker MP3
```

2. If you do not already have the virtual environment, create it:

```powershell
python -m venv .venv
```

3. Install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Start the app:

```powershell
.\run_server.ps1
```

5. Open the site in your browser:

```text
http://127.0.0.1:8000
```

Leave the PowerShell window open while you use the app. Stop it later with `Ctrl + C`.

## Set Up Your Keys

Put your keys in `.env` in the project root.

Use this shape:

```env
OPENAI_API_KEY=your_openai_key_here
OPENAI_TEXT_MODEL=gpt-4.1-mini
OPENAI_TTS_MODEL=gpt-4o-mini-tts

ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

OUTPUT_DIR=generated
```

`OPENAI_API_KEY` is required. The ElevenLabs values can stay blank for now.

## How To Use

1. Type your scary story idea into the story box.
2. Pick the story length.
3. Pick the OpenAI voice.
4. Pick a background ambience option.
5. Set the background volume if you want ambience mixed in.
6. Click `Generate MP3`.

The app will:

1. Write an original scary story.
2. Generate narration audio.
3. Mix in the selected ambience MP3 if you chose one and the volume is above `0%`.
4. Show the story text and a downloadable MP3.

## Ambience Files

Put these files in the `ambience` folder with these exact names:

```text
rain.mp3
stormy-rain.mp3
campfire.mp3
urban-scare.mp3
woods-night.mp3
old-house.mp3
```

## Notes

1. `none` means no background ambience.
2. If you add or replace ambience files, restart the server.
3. If something looks stale in the browser, hard refresh with `Ctrl + F5`.
