import os
import base64
import time
from threading import Lock
from flask import Flask, render_template_string, request, jsonify, Response

app = Flask(__name__)
state_lock = Lock()
latest_frame = {
    "bytes": b"",
    "content_type": "image/jpeg",
    "seq": 0,
    "ts": 0.0,
    "cached_b64": None,
}

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
      object-fit: contain !important;
    }

    .frame:fullscreen .pill {
      right: 18px;
      top: 18px;
    }

    .frame-actions {
      position: absolute;
      left: 12px;
      top: 12px;
      z-index: 6;
      display: none;
      gap: 8px;
    }

    .frame-action-btn {
      border: 1px solid var(--panel-border);
      background: rgba(6, 22, 27, 0.82);
      color: var(--text);
      padding: 7px 11px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
    }

    .frame:fullscreen .frame-actions {
      display: flex;
      left: 18px;
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

    .crop-overlay {
      position: absolute;
      inset: 0;
      background: rgba(3, 10, 12, 0.84);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 30;
      padding: 14px;
    }

    .crop-overlay.active {
      display: flex;
    }

    .crop-overlay.fullscreen-crop {
      padding: 0;
      align-items: stretch;
      justify-content: stretch;
      background: rgba(0, 0, 0, 0.72);
    }

    .crop-panel {
      width: min(1100px, 100%);
      max-height: 100%;
      overflow: hidden;
      background: rgba(10, 28, 33, 0.95);
      border: 1px solid var(--panel-border);
      border-radius: 16px;
      box-shadow: var(--shadow);
      display: grid;
      grid-template-rows: auto 1fr auto;
    }

    .crop-overlay.fullscreen-crop .crop-panel {
      width: 100%;
      max-width: none;
      height: 100%;
      max-height: none;
      border-radius: 0;
      border: none;
    }

    .crop-overlay.fullscreen-crop .crop-stage {
      padding: 8px;
    }

    .crop-head {
      padding: 12px 14px;
      border-bottom: 1px solid var(--panel-border);
      color: var(--muted);
      font-size: .9rem;
    }

    .crop-stage {
      padding: 12px;
      overflow: auto;
    }

    .crop-canvas-wrap {
      position: relative;
      width: fit-content;
      margin: 0 auto;
      border: 1px solid var(--panel-border);
      border-radius: 10px;
      overflow: hidden;
      background: #000;
    }

    #cropCanvas {
      display: block;
      max-width: 100%;
      height: auto;
      cursor: crosshair;
      user-select: none;
    }

    .crop-selection {
      display: none;
      position: absolute;
      border: 2px solid var(--accent);
      background: rgba(23, 217, 163, 0.12);
      box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.35);
      pointer-events: none;
    }

    .crop-foot {
      padding: 12px 14px;
      border-top: 1px solid var(--panel-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }

    .crop-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .crop-status {
      color: var(--muted);
      font-size: .88rem;
      min-height: 1.2em;
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
        <button id="captureBtn" type="button">Capturar</button>
        <button id="fitBtn" type="button" data-active="false">Ajustar Alto</button>
        <button id="fullscreenBtn" type="button">Pantalla Completa</button>
        <label class="rate">
          Refresco
          <input id="rateInput" type="range" min="120" max="1500" step="20" value="350" />
          <span id="rateLabel">350ms</span>
        </label>
      </div>
    </header>

    <section class="stage">
      <div class="frame">
        <div class="frame-actions">
          <button id="captureFsBtn" type="button" class="frame-action-btn">Capturar</button>
        </div>
        <span class="pill" id="modeLabel">Modo: ancho</span>
        <img id="img" src="" alt="Captura remota" />
        <div id="empty" class="empty">
          Esperando frames. Si no aparece imagen, revisá permisos de grabación de pantalla en macOS.
        </div>
        <div id="cropOverlay" class="crop-overlay" aria-hidden="true">
          <div class="crop-panel">
            <div class="crop-head">Arrastrá para seleccionar el recorte y luego copiá al portapapeles.</div>
            <div class="crop-stage">
              <div class="crop-canvas-wrap">
                <canvas id="cropCanvas"></canvas>
                <div id="cropSelection" class="crop-selection"></div>
              </div>
            </div>
            <div class="crop-foot">
              <span id="cropStatus" class="crop-status"></span>
              <div class="crop-actions">
                <button id="resetCropBtn" type="button">Reiniciar</button>
                <button id="cancelCropBtn" type="button">Cancelar</button>
                <button id="copyCropBtn" type="button">Copiar Recorte</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <footer class="footer">
      Atajos: tecla F pantalla completa, tecla C capturar.
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
    const captureBtn = document.getElementById("captureBtn");
    const captureFsBtn = document.getElementById("captureFsBtn");
    const fitBtn = document.getElementById("fitBtn");
    const modeLabel = document.getElementById("modeLabel");
    const fullscreenBtn = document.getElementById("fullscreenBtn");
    const rateInput = document.getElementById("rateInput");
    const rateLabel = document.getElementById("rateLabel");
    const cropOverlay = document.getElementById("cropOverlay");
    const cropCanvas = document.getElementById("cropCanvas");
    const cropSelection = document.getElementById("cropSelection");
    const cropStatus = document.getElementById("cropStatus");
    const copyCropBtn = document.getElementById("copyCropBtn");
    const cancelCropBtn = document.getElementById("cancelCropBtn");
    const resetCropBtn = document.getElementById("resetCropBtn");
    const cropCtx = cropCanvas.getContext("2d");

    let fitHeight = false;
    let timer = null;
    let pollMs = 350;
    let frameCount = 0;
    let lastFrameTime = 0;
    let currentSeq = 0;
    let reqInFlight = false;
    let fpsWindowStart = performance.now();
    let cropImage = null;
    let dragStart = null;
    let dragCurrent = null;
    let cropRect = null;
    let cropScaleX = 1;
    let cropScaleY = 1;

    function updateStatus(online) {
      dot.classList.toggle("online", online);
      statusText.textContent = online ? "En línea" : "Sin señal";
    }

    function setCropStatus(message) {
      cropStatus.textContent = message;
    }

    function normalizeRect(a, b) {
      const x = Math.min(a.x, b.x);
      const y = Math.min(a.y, b.y);
      const w = Math.abs(a.x - b.x);
      const h = Math.abs(a.y - b.y);
      return { x, y, w, h };
    }

    function resetCropRect() {
      dragStart = null;
      dragCurrent = null;
      cropRect = null;
      cropSelection.style.display = "none";
      setCropStatus("");
    }

    function closeCropOverlay() {
      cropOverlay.classList.remove("active");
      cropOverlay.setAttribute("aria-hidden", "true");
      resetCropRect();
    }

    function getCanvasPoint(event) {
      const rect = cropCanvas.getBoundingClientRect();
      const x = Math.max(0, Math.min(event.clientX - rect.left, rect.width));
      const y = Math.max(0, Math.min(event.clientY - rect.top, rect.height));
      return { x, y };
    }

    function drawSelection() {
      if (!dragStart || !dragCurrent) {
        return;
      }
      cropRect = normalizeRect(dragStart, dragCurrent);
      if (cropRect.w < 2 || cropRect.h < 2) {
        cropSelection.style.display = "none";
        return;
      }
      cropSelection.style.display = "block";
      cropSelection.style.left = cropRect.x + "px";
      cropSelection.style.top = cropRect.y + "px";
      cropSelection.style.width = cropRect.w + "px";
      cropSelection.style.height = cropRect.h + "px";
      setCropStatus("Seleccion: " + Math.round(cropRect.w * cropScaleX) + "x" + Math.round(cropRect.h * cropScaleY) + " px");
    }

    function openCropOverlay() {
      if (!img.src || !img.naturalWidth || !img.naturalHeight) {
        setCropStatus("No hay imagen para capturar.");
        return;
      }

      const snapshot = new Image();
      snapshot.onload = () => {
        cropImage = snapshot;
        const isFullscreenCapture = document.fullscreenElement === frame;
        cropOverlay.classList.toggle("fullscreen-crop", isFullscreenCapture);
        const frameRect = frame.getBoundingClientRect();
        const maxW = Math.max(300, Math.floor(frameRect.width * (isFullscreenCapture ? 0.995 : 0.94)));
        const maxH = Math.max(220, Math.floor(frameRect.height * (isFullscreenCapture ? 0.92 : 0.8)));
        const maxRatio = isFullscreenCapture ? 2 : 1;
        const ratio = Math.min(maxW / snapshot.naturalWidth, maxH / snapshot.naturalHeight, maxRatio);
        cropCanvas.width = Math.max(1, Math.round(snapshot.naturalWidth * ratio));
        cropCanvas.height = Math.max(1, Math.round(snapshot.naturalHeight * ratio));
        cropScaleX = snapshot.naturalWidth / cropCanvas.width;
        cropScaleY = snapshot.naturalHeight / cropCanvas.height;
        cropCtx.drawImage(snapshot, 0, 0, cropCanvas.width, cropCanvas.height);
        resetCropRect();
        setCropStatus("Fuente: " + snapshot.naturalWidth + "x" + snapshot.naturalHeight + " px");
        cropOverlay.classList.add("active");
        cropOverlay.setAttribute("aria-hidden", "false");
      };
      snapshot.onerror = () => {
        setCropStatus("No se pudo preparar la captura.");
      };
      snapshot.src = img.src;
    }

    async function startCaptureFlow() {
      openCropOverlay();
    }

    function applyFitMode() {
      const isFrameFullscreen = document.fullscreenElement === frame;
      if (isFrameFullscreen) {
        img.style.height = "100vh";
        img.style.objectFit = "contain";
      } else {
        img.style.height = fitHeight ? "70vh" : "auto";
        img.style.objectFit = fitHeight ? "contain" : "cover";
      }
      fitBtn.dataset.active = fitHeight ? "true" : "false";
      modeLabel.textContent = fitHeight ? "Modo: alto" : "Modo: ancho";
    }

    async function fetchFrame() {
      if (reqInFlight) {
        return;
      }
      reqInFlight = true;
      try {
        const res = await fetch("/frame-meta", { cache: "no-store" });
        if (!res.ok) {
          updateStatus(false);
          return;
        }

        const meta = await res.json();
        if (!meta.has_frame) {
          updateStatus(false);
          return;
        }

        if (meta.seq !== currentSeq) {
          currentSeq = meta.seq;
          const ts = Date.now();
          img.src = "/frame?seq=" + currentSeq + "&t=" + ts;
          empty.style.display = "none";
          frameCount += 1;
          lastFrameTime = ts;
          lastUpdate.textContent = "Última actualización: " + new Date(ts).toLocaleTimeString();
          updateStatus(true);
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

    captureBtn.addEventListener("click", () => {
      startCaptureFlow();
    });

    captureFsBtn.addEventListener("click", () => {
      startCaptureFlow();
    });

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

    document.addEventListener("fullscreenchange", () => {
      applyFitMode();
    });

    rateInput.addEventListener("input", () => {
      pollMs = Number(rateInput.value);
      rateLabel.textContent = pollMs + "ms";
      startPolling();
    });

    cropCanvas.addEventListener("pointerdown", (event) => {
      if (!cropOverlay.classList.contains("active")) {
        return;
      }
      dragStart = getCanvasPoint(event);
      dragCurrent = dragStart;
      drawSelection();
      cropCanvas.setPointerCapture(event.pointerId);
    });

    cropCanvas.addEventListener("pointermove", (event) => {
      if (!dragStart) {
        return;
      }
      dragCurrent = getCanvasPoint(event);
      drawSelection();
    });

    cropCanvas.addEventListener("pointerup", () => {
      dragStart = null;
      dragCurrent = null;
    });

    cropCanvas.addEventListener("pointercancel", () => {
      dragStart = null;
      dragCurrent = null;
    });

    resetCropBtn.addEventListener("click", resetCropRect);

    cancelCropBtn.addEventListener("click", closeCropOverlay);

    copyCropBtn.addEventListener("click", async () => {
      if (!cropRect || cropRect.w < 2 || cropRect.h < 2 || !cropImage) {
        setCropStatus("Primero selecciona un area para recortar.");
        return;
      }
      const sx = Math.max(0, Math.floor(cropRect.x * cropScaleX));
      const sy = Math.max(0, Math.floor(cropRect.y * cropScaleY));
      const sw = Math.min(cropImage.naturalWidth - sx, Math.ceil(cropRect.w * cropScaleX));
      const sh = Math.min(cropImage.naturalHeight - sy, Math.ceil(cropRect.h * cropScaleY));

      if (sw <= 0 || sh <= 0) {
        setCropStatus("El recorte no es valido.");
        return;
      }

      const outCanvas = document.createElement("canvas");
      outCanvas.width = sw;
      outCanvas.height = sh;
      outCanvas.getContext("2d").drawImage(cropImage, sx, sy, sw, sh, 0, 0, sw, sh);

      const blob = await new Promise((resolve) => outCanvas.toBlob(resolve, "image/png"));
      if (!blob) {
        setCropStatus("No se pudo generar la imagen.");
        return;
      }

      if (!navigator.clipboard || !window.ClipboardItem) {
        setCropStatus("Tu navegador no soporta copiar imagenes al portapapeles.");
        return;
      }

      try {
        await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
        setCropStatus("Recorte copiado. Ahora pega con Ctrl+V o Cmd+V.");
        setTimeout(closeCropOverlay, 450);
      } catch (error) {
        setCropStatus("No se pudo copiar. Revisa permisos del portapapeles.");
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key.toLowerCase() === "f") {
        fullscreenBtn.click();
      } else if (event.key.toLowerCase() === "c") {
        startCaptureFlow();
      } else if (event.key === "Escape" && cropOverlay.classList.contains("active")) {
        closeCropOverlay();
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
    frame_bytes = b""
    content_type = "image/jpeg"

    if request.is_json:
        payload = request.get_json(silent=True) or {}
        encoded = payload.get("image", "")
        if not encoded:
            return jsonify({"ok": False, "error": "missing image"}), 400
        try:
            frame_bytes = base64.b64decode(encoded)
        except Exception:
            return jsonify({"ok": False, "error": "invalid base64"}), 400
    elif "frame" in request.files:
        uploaded = request.files["frame"]
        frame_bytes = uploaded.read()
        if uploaded.mimetype:
            content_type = uploaded.mimetype
    elif request.data:
        frame_bytes = request.data
        if request.mimetype:
            content_type = request.mimetype
    else:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    if not frame_bytes:
        return jsonify({"ok": False, "error": "empty frame"}), 400

    with state_lock:
        latest_frame["bytes"] = frame_bytes
        latest_frame["content_type"] = content_type or "image/jpeg"
        latest_frame["seq"] += 1
        latest_frame["ts"] = time.time()
        latest_frame["cached_b64"] = None
        seq = latest_frame["seq"]

    return jsonify({"ok": True, "seq": seq})


@app.route("/frame-meta")
def frame_meta():
    with state_lock:
        has_frame = bool(latest_frame["bytes"])
        seq = latest_frame["seq"]
        ts = latest_frame["ts"]
        content_type = latest_frame["content_type"]
        size = len(latest_frame["bytes"]) if has_frame else 0

    return jsonify(
        {
            "has_frame": has_frame,
            "seq": seq,
            "ts": ts,
            "content_type": content_type,
            "size_bytes": size,
        }
    )


@app.route("/frame")
def frame():
    with state_lock:
        frame_bytes = latest_frame["bytes"]
        content_type = latest_frame["content_type"]

    if not frame_bytes:
        return Response(status=404)

    response = Response(frame_bytes, mimetype=content_type)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/latest")
def latest():
    # Compatibilidad con clientes viejos que esperan base64 plano.
    with state_lock:
        if not latest_frame["bytes"]:
            return ""
        if latest_frame["cached_b64"] is None:
            latest_frame["cached_b64"] = base64.b64encode(latest_frame["bytes"]).decode("utf-8")
        return latest_frame["cached_b64"]


@app.route("/health")
def health():
    with state_lock:
        has_frame = bool(latest_frame["bytes"])
        seq = latest_frame["seq"]
        ts = latest_frame["ts"]
    return jsonify({"ok": True, "has_frame": has_frame, "seq": seq, "ts": ts})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
