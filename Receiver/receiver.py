import os
from flask import Flask, render_template_string, request

app = Flask(__name__)
latest_image = ""

HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MCStation Receiver</title>
  <style>
    :root {
      --bg-0: #06161b;
      --bg-1: #0e2a31;
      --panel: rgba(11, 32, 38, 0.72);
      --panel-border: rgba(133, 190, 195, 0.22);
      --text: #e6f2f3;
      --muted: #9fb8bb;
      --accent: #17d9a3;
      --warn: #f0b14a;
      --danger: #f06f52;
      --shadow: 0 20px 50px rgba(2, 9, 11, 0.45);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      background:
        radial-gradient(1200px 700px at 0% -20%, #1a4e5b 0%, transparent 55%),
        radial-gradient(1200px 800px at 100% 120%, #103c47 0%, transparent 58%),
        linear-gradient(135deg, var(--bg-0), var(--bg-1));
      display: grid;
      place-items: center;
      padding: 24px;
    }

    .app {
      width: min(1200px, 100%);
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 20px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      overflow: hidden;
      animation: reveal 380ms ease-out;
    }

    .topbar {
      padding: 16px 18px;
      border-bottom: 1px solid var(--panel-border);
      display: flex;
      gap: 14px;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
    }

    .title-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .dot {
      width: 11px;
      height: 11px;
      border-radius: 999px;
      background: var(--danger);
      box-shadow: 0 0 0 0 rgba(240, 111, 82, 0.7);
      transition: background .2s ease, box-shadow .2s ease;
    }

    .dot.online {
      background: var(--accent);
      box-shadow: 0 0 0 6px rgba(23, 217, 163, 0.18);
    }

    h1 {
      margin: 0;
      font-size: clamp(1rem, 2vw, 1.3rem);
      font-weight: 700;
      letter-spacing: .2px;
    }

    .meta {
      display: flex;
      gap: 8px 14px;
      align-items: center;
      color: var(--muted);
      font-size: .92rem;
      flex-wrap: wrap;
    }

    .controls {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }

    button {
      border: 1px solid var(--panel-border);
      background: rgba(14, 42, 49, 0.9);
      color: var(--text);
      padding: 9px 12px;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: transform .12s ease, border-color .12s ease, background .12s ease;
    }

    button:hover {
      transform: translateY(-1px);
      border-color: rgba(133, 190, 195, 0.55);
      background: rgba(18, 52, 60, 0.96);
    }

    button[data-active="true"] {
      border-color: rgba(23, 217, 163, 0.6);
      background: rgba(23, 217, 163, 0.13);
    }

    .rate {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-left: 4px;
      font-size: .9rem;
      color: var(--muted);
    }

    input[type="range"] {
      accent-color: var(--accent);
    }

    .stage {
      padding: 16px;
    }

    .frame {
      width: 100%;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid var(--panel-border);
      background:
        repeating-linear-gradient(
          -45deg,
          rgba(255, 255, 255, 0.04),
          rgba(255, 255, 255, 0.04) 12px,
          rgba(255, 255, 255, 0.02) 12px,
          rgba(255, 255, 255, 0.02) 24px
        );
      min-height: 260px;
      display: grid;
      place-items: center;
      position: relative;
      isolation: isolate;
    }

    .frame:fullscreen {
      width: 100vw;
      height: 100vh;
      max-width: none;
      max-height: none;
      border: none;
      border-radius: 0;
      margin: 0;
      padding: 0;
      background: #000;
    }

    .frame:fullscreen img {
      width: 100vw;
      height: 100vh;
      object-fit: contain;
    }

    .frame:fullscreen .pill {
      right: 18px;
      top: 18px;
    }

    img {
      display: block;
      width: 100%;
      height: auto;
      object-fit: contain;
    }

    .empty {
      color: var(--muted);
      font-size: .95rem;
      padding: 24px;
      text-align: center;
      max-width: 42ch;
    }

    .pill {
      position: absolute;
      right: 12px;
      top: 12px;
      font-size: 0.78rem;
      background: rgba(6, 22, 27, .82);
      border: 1px solid var(--panel-border);
      color: var(--muted);
      border-radius: 999px;
      padding: 6px 10px;
      backdrop-filter: blur(4px);
    }

    .footer {
      padding: 10px 16px 14px;
      color: var(--muted);
      font-size: .8rem;
      border-top: 1px solid var(--panel-border);
    }

    @keyframes reveal {
      from {
        opacity: 0;
        transform: translateY(8px) scale(0.99);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    @media (max-width: 720px) {
      body {
        padding: 12px;
      }
      .topbar {
        padding: 12px;
      }
      .stage {
        padding: 10px;
      }
      .meta {
        font-size: .85rem;
      }
      .footer {
        font-size: .74rem;
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <header class="topbar">
      <div class="title-wrap">
        <span id="statusDot" class="dot"></span>
        <h1>Captura En Tiempo Real</h1>
      </div>
      <div class="meta">
        <span id="statusText">Sin señal</span>
        <span id="lastUpdate">Última actualización: -</span>
        <span id="fps">0.0 fps</span>
      </div>
      <div class="controls">
        <button id="fitBtn" type="button" data-active="false">Ajustar Alto</button>
        <button id="fullscreenBtn" type="button">Pantalla Completa</button>
        <label class="rate">
          Refresco
          <input id="rateInput" type="range" min="120" max="1500" step="20" value="500" />
          <span id="rateLabel">500ms</span>
        </label>
      </div>
    </header>

    <section class="stage">
      <div class="frame">
        <span class="pill" id="modeLabel">Modo: ancho</span>
        <img id="img" src="" alt="Captura remota" />
        <div id="empty" class="empty">
          Esperando frames. Si no aparece imagen, revisá permisos de grabación de pantalla en macOS.
        </div>
      </div>
    </section>

    <footer class="footer">
      Atajos: tecla F pantalla completa.
    </footer>
  </main>

  <script>
    const img = document.getElementById("img");
    const frame = document.querySelector(".frame");
    const empty = document.getElementById("empty");
    const dot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");
    const lastUpdate = document.getElementById("lastUpdate");
    const fps = document.getElementById("fps");
    const fitBtn = document.getElementById("fitBtn");
    const modeLabel = document.getElementById("modeLabel");
    const fullscreenBtn = document.getElementById("fullscreenBtn");
    const rateInput = document.getElementById("rateInput");
    const rateLabel = document.getElementById("rateLabel");

    let fitHeight = false;
    let timer = null;
    let pollMs = 500;
    let frameCount = 0;
    let lastFrameTime = 0;
    let lastData = "";
    let reqInFlight = false;
    let fpsWindowStart = performance.now();

    function updateStatus(online) {
      dot.classList.toggle("online", online);
      statusText.textContent = online ? "En línea" : "Sin señal";
    }

    function applyFitMode() {
      img.style.height = fitHeight ? "70vh" : "auto";
      img.style.objectFit = fitHeight ? "contain" : "cover";
      fitBtn.dataset.active = fitHeight ? "true" : "false";
      modeLabel.textContent = fitHeight ? "Modo: alto" : "Modo: ancho";
    }

    async function fetchFrame() {
      if (reqInFlight) {
        return;
      }
      reqInFlight = true;
      try {
        const res = await fetch("/latest", { cache: "no-store" });
        const data = await res.text();
        if (data && data !== lastData) {
          lastData = data;
          img.src = "data:image/jpeg;base64," + data;
          empty.style.display = "none";
          frameCount += 1;
          lastFrameTime = Date.now();
          lastUpdate.textContent = "Última actualización: " + new Date(lastFrameTime).toLocaleTimeString();
          updateStatus(true);
        } else if (!data) {
          updateStatus(false);
        }

        const now = performance.now();
        const elapsed = (now - fpsWindowStart) / 1000;
        if (elapsed >= 1) {
          fps.textContent = (frameCount / elapsed).toFixed(1) + " fps";
          frameCount = 0;
          fpsWindowStart = now;
        }

        if (lastFrameTime && Date.now() - lastFrameTime > Math.max(pollMs * 4, 2500)) {
          updateStatus(false);
        }
      } catch (err) {
        updateStatus(false);
      } finally {
        reqInFlight = false;
      }
    }

    function startPolling() {
      if (timer) {
        clearInterval(timer);
      }
      timer = setInterval(fetchFrame, pollMs);
    }

    fitBtn.addEventListener("click", () => {
      fitHeight = !fitHeight;
      applyFitMode();
    });

    fullscreenBtn.addEventListener("click", async () => {
      if (!document.fullscreenElement) {
        await frame.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    });

    rateInput.addEventListener("input", () => {
      pollMs = Number(rateInput.value);
      rateLabel.textContent = pollMs + "ms";
      startPolling();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key.toLowerCase() === "f") {
        fullscreenBtn.click();
      }
    });

    applyFitMode();
    startPolling();
    fetchFrame();
  </script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/upload", methods=["POST"])
def upload():
    global latest_image
    latest_image = request.json['image']
    return "OK"

@app.route("/latest")
def latest():
    return latest_image

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
