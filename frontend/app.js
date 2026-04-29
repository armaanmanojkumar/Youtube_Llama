const status = {
  ingest: document.getElementById("ingestStatus"),
  query: document.getElementById("queryStatus"),
};
const videoUrl = document.getElementById("videoUrl");
const queryText = document.getElementById("queryText");
const modelSelect = document.getElementById("modelSelect");
const topK = document.getElementById("topK");
const answer = document.getElementById("answer");
const sources = document.getElementById("sources");
const videosList = document.getElementById("videosList");
const videoCount = document.getElementById("videoCount");
const chunkCount = document.getElementById("chunkCount");
const responseAvg = document.getElementById("responseAvg");
const recentQueries = document.getElementById("recentQueries");
const ingestButton = document.getElementById("ingestButton");
const queryButton = document.getElementById("queryButton");
const refreshVideos = document.getElementById("refreshVideos");

const API_BASE = "/";

function setStatus(type, message, isError = false) {
  const target = status[type];
  if (!target) return;
  target.textContent = message;
  target.style.color = isError ? "#ff8b8b" : "#b7c0ff";
}

function clearAnswer() {
  answer.textContent = "Submit a question to see the AI answer here.";
  answer.classList.add("empty");
  sources.innerHTML = "";
}

async function getModels() {
  try {
    const res = await fetch(`${API_BASE}models`);
    const body = await res.json();
    modelSelect.innerHTML = "";
    (body.models || []).forEach((model) => {
      const option = document.createElement("option");
      option.value = model;
      option.textContent = model;
      if (model === body.current) option.selected = true;
      modelSelect.appendChild(option);
    });
  } catch (error) {
    setStatus("query", "Unable to load models. Make sure the backend is running.", true);
  }
}

async function fetchLibrary() {
  try {
    const [videoRes, statsRes, perfRes] = await Promise.all([
      fetch(`${API_BASE}videos`),
      fetch(`${API_BASE}stats`),
      fetch(`${API_BASE}performance`),
    ]);
    const videos = await videoRes.json();
    const stats = await statsRes.json();
    const perf = await perfRes.json();
    videosList.innerHTML = videos.length
      ? videos.map((video) => `
          <div class="video-item">
            <h3>${video.video_id}</h3>
            <a href="${video.video_url}" target="_blank" rel="noreferrer">Watch on YouTube</a>
          </div>
        `).join("")
      : "<p>No videos indexed yet.</p>";
    videoCount.textContent = stats.total_videos ?? 0;
    chunkCount.textContent = stats.total_chunks ?? 0;
    responseAvg.textContent = `${(perf.summary?.[0]?.avg_time_s || 0).toFixed(2)}s`;
    recentQueries.innerHTML = perf.records.length
      ? perf.records.slice(-5).reverse().map((record) => `
          <li><strong>${record.query}</strong><br />${record.model} · ${record.response_time_s}s</li>
        `).join("")
      : "<li>No recent queries.</li>";
  } catch (error) {
    setStatus("query", "Unable to refresh library.", true);
  }
}

async function ingestVideo() {
  const url = videoUrl.value.trim();
  if (!url) {
    setStatus("ingest", "Please enter a valid YouTube URL.", true);
    return;
  }

  setStatus("ingest", "Indexing video…");
  ingestButton.disabled = true;
  try {
    const response = await fetch(`${API_BASE}ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Indexing failed.");
    setStatus("ingest", `Indexed ${body.video_id} with ${body.chunks_indexed} chunks.`);
    await fetchLibrary();
  } catch (error) {
    setStatus("ingest", error.message, true);
  } finally {
    ingestButton.disabled = false;
  }
}

async function askQuery() {
  const query = queryText.value.trim();
  if (!query) {
    setStatus("query", "Enter a question before sending.", true);
    return;
  }

  setStatus("query", "Querying videos…");
  queryButton.disabled = true;
  answer.classList.remove("empty");
  answer.textContent = "Thinking...";
  sources.innerHTML = "";

  try {
    const response = await fetch(`${API_BASE}query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        top_k: Number(topK.value) || 4,
        model: modelSelect.value,
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Query failed.");
    answer.textContent = body.answer || "No answer received.";
    setStatus("query", `Completed in ${body.meta.response_time_s}s with ${body.meta.chunks} chunks.`);
    sources.innerHTML = body.sources.map((source) => `
      <div class="source-card">
        <a href="${source.video_url}&t=${Math.floor(source.start_time || 0)}" target="_blank" rel="noreferrer">
          ${source.video_id} · ${source.start_time ? `${Math.floor(source.start_time / 60)}m${Math.floor(source.start_time % 60)}s` : "unknown"}
        </a>
        <p>${source.chunk}</p>
      </div>
    `).join("");
    await fetchLibrary();
  } catch (error) {
    answer.textContent = "Unable to get an answer.";
    setStatus("query", error.message, true);
  } finally {
    queryButton.disabled = false;
  }
}

ingestButton.addEventListener("click", ingestVideo);
queryButton.addEventListener("click", askQuery);
refreshVideos.addEventListener("click", fetchLibrary);

window.addEventListener("load", async () => {
  await Promise.all([getModels(), fetchLibrary()]);
  clearAnswer();
});
