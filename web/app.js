const form = document.querySelector("#story-form");
const button = document.querySelector("#generate-button");
const statusEl = document.querySelector("#status");
const titleEl = document.querySelector("#title");
const storyEl = document.querySelector("#story");
const player = document.querySelector("#player");
const download = document.querySelector("#download");

function setBusy(isBusy) {
  button.disabled = isBusy;
  button.textContent = isBusy ? "Generating..." : "Generate MP3";
}

function setStatus(message) {
  statusEl.textContent = message;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const payload = {
    topic: data.get("topic").trim(),
    length: data.get("length"),
    style: data.get("style"),
    voice: data.get("voice"),
  };

  setBusy(true);
  setStatus("Writing story and rendering narration...");
  player.hidden = true;
  download.hidden = true;

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail || "Generation failed.");
    }

    titleEl.textContent = body.title;
    storyEl.textContent = body.story;
    player.src = body.audio_url;
    player.hidden = false;
    download.href = body.audio_url;
    download.download = body.filename;
    download.hidden = false;
    setStatus("Complete");
  } catch (error) {
    setStatus(error.message);
  } finally {
    setBusy(false);
  }
});
