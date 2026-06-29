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

function getErrorMessage(body) {
  if (typeof body.detail === "string") {
    return body.detail;
  }

  if (Array.isArray(body.detail)) {
    return body.detail
      .map((error) => {
        const field = Array.isArray(error.loc) ? error.loc.join(".") : "request";
        return `${field}: ${error.msg}`;
      })
      .join(" ");
  }

  return "Generation failed.";
}

async function readResponseBody(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return { detail: text || response.statusText };
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

    const body = await readResponseBody(response);
    if (!response.ok) {
      throw new Error(getErrorMessage(body));
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
