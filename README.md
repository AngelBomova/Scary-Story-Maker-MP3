# Scary Story MP3 Maker

A local web app that writes a scary story from a prompt, turns it into an MP3, and gives you an audio player plus download link.

## Setup

1. Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Open `.env` and paste your API keys into the empty spots.

4. Run the app:

```powershell
.\run_server.ps1
```

Then open `http://127.0.0.1:8000`.

## API Keys

Keep real keys in `.env`. The `.gitignore` file keeps `.env` out of version control.

`OPENAI_API_KEY` is required. `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` are optional. If ElevenLabs values are blank, the app uses OpenAI text-to-speech.
