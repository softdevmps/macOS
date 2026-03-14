import os
import time
import base64
from io import BytesIO

import pyautogui
import requests
from PIL import Image, ImageChops, ImageStat

SERVER_URL = os.getenv("SERVER_URL", "https://screen-receiver.onrender.com/upload")

PROFILE = os.getenv("PROFILE", "wifi_balanced").strip().lower()

if PROFILE == "low_bandwidth":
    default_fps = 0.8
    default_quality = 45
    default_width = 1024
elif PROFILE == "quality":
    default_fps = 1.2
    default_quality = 68
    default_width = 1600
else:
    default_fps = 1.0
    default_quality = 55
    default_width = 1280

TARGET_FPS = float(os.getenv("TARGET_FPS", str(default_fps)))
BASE_INTERVAL = 1.0 / max(TARGET_FPS, 0.1)
MAX_BACKOFF_SECONDS = float(os.getenv("MAX_BACKOFF_SECONDS", "5.0"))

BASE_JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", str(default_quality)))
MIN_JPEG_QUALITY = int(os.getenv("MIN_JPEG_QUALITY", "30"))
MAX_JPEG_QUALITY = int(os.getenv("MAX_JPEG_QUALITY", "80"))

MAX_WIDTH = int(os.getenv("MAX_WIDTH", str(default_width)))
MAX_HEIGHT = int(os.getenv("MAX_HEIGHT", "0"))
CHANGE_THRESHOLD = float(os.getenv("CHANGE_THRESHOLD", "2.5"))
MAX_PAYLOAD_KB = int(os.getenv("MAX_PAYLOAD_KB", "320"))

CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "3"))
READ_TIMEOUT = float(os.getenv("READ_TIMEOUT", "8"))
UPLOAD_MODE = os.getenv("UPLOAD_MODE", "auto").strip().lower()  # auto|multipart|json

STATS_EVERY_SECONDS = float(os.getenv("STATS_EVERY_SECONDS", "10"))


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def normalize_image(image: Image.Image) -> Image.Image:
    if image.mode != "RGB":
        image = image.convert("RGB")

    w, h = image.size
    ratios = [1.0]
    if MAX_WIDTH > 0:
        ratios.append(MAX_WIDTH / float(w))
    if MAX_HEIGHT > 0:
        ratios.append(MAX_HEIGHT / float(h))

    ratio = min(ratios)
    if ratio < 1.0:
        new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    return image


def mini_diff_score(current: Image.Image, previous_thumb: Image.Image):
    thumb = current.resize((64, 36), Image.Resampling.BILINEAR).convert("L")
    if previous_thumb is None:
        return thumb, 999.0

    diff = ImageChops.difference(thumb, previous_thumb)
    score = ImageStat.Stat(diff).mean[0]
    return thumb, score


def encode_jpeg(image: Image.Image, quality: int) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def post_multipart(session: requests.Session, payload: bytes) -> requests.Response:
    files = {"frame": ("frame.jpg", payload, "image/jpeg")}
    return session.post(
        SERVER_URL,
        files=files,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
    )


def post_json(session: requests.Session, payload: bytes) -> requests.Response:
    encoded = base64.b64encode(payload).decode("utf-8")
    return session.post(
        SERVER_URL,
        json={"image": encoded},
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
    )


def send_frame(session: requests.Session, payload: bytes, mode: str):
    if mode == "multipart":
        return post_multipart(session, payload), "multipart"

    if mode == "json":
        return post_json(session, payload), "json"

    # auto mode: prueba multipart y cae a json si el servidor no lo soporta.
    response = post_multipart(session, payload)
    if response.status_code in (400, 404, 405, 415):
        response = post_json(session, payload)
        return response, "json"
    return response, "multipart"


def capturar_y_enviar():
    session = requests.Session()

    current_quality = clamp(BASE_JPEG_QUALITY, MIN_JPEG_QUALITY, MAX_JPEG_QUALITY)
    current_interval = BASE_INTERVAL
    current_mode = UPLOAD_MODE

    previous_thumb = None
    sent_count = 0
    skipped_count = 0
    error_count = 0
    consecutive_errors = 0

    last_report_at = time.time()
    last_kb = 0.0
    last_rtt_ms = 0.0
    last_diff_score = 0.0

    print(
        "Sender iniciado:",
        f"profile={PROFILE}",
        f"fps={TARGET_FPS:.2f}",
        f"q={current_quality}",
        f"max_width={MAX_WIDTH}",
        f"max_height={MAX_HEIGHT}",
        f"upload_mode={UPLOAD_MODE}",
        f"server={SERVER_URL}",
    )

    while True:
        loop_started = time.time()

        try:
            screenshot = pyautogui.screenshot()
            screenshot = normalize_image(screenshot)

            thumb, diff_score = mini_diff_score(screenshot, previous_thumb)
            last_diff_score = diff_score

            if diff_score < CHANGE_THRESHOLD:
                skipped_count += 1
            else:
                previous_thumb = thumb
                payload = encode_jpeg(screenshot, current_quality)
                payload_kb = len(payload) / 1024.0

                req_started = time.time()
                response, used_mode = send_frame(session, payload, current_mode)
                rtt = time.time() - req_started

                if response.ok:
                    sent_count += 1
                    consecutive_errors = 0
                    last_kb = payload_kb
                    last_rtt_ms = rtt * 1000.0
                    current_mode = used_mode

                    # Ajuste adaptativo para wifi inestable.
                    if payload_kb > MAX_PAYLOAD_KB:
                        current_quality = clamp(current_quality - 4, MIN_JPEG_QUALITY, MAX_JPEG_QUALITY)
                    elif payload_kb < (MAX_PAYLOAD_KB * 0.55) and rtt < (BASE_INTERVAL * 0.7):
                        current_quality = clamp(current_quality + 1, MIN_JPEG_QUALITY, MAX_JPEG_QUALITY)

                    if rtt > (current_interval * 1.6):
                        current_interval = min(current_interval * 1.15, MAX_BACKOFF_SECONDS)
                    else:
                        current_interval = max(BASE_INTERVAL, current_interval * 0.95)
                else:
                    error_count += 1
                    consecutive_errors += 1
                    current_interval = min(current_interval * 1.35, MAX_BACKOFF_SECONDS)
                    current_quality = clamp(current_quality - 2, MIN_JPEG_QUALITY, MAX_JPEG_QUALITY)
                    print(f"Upload rechazado: status={response.status_code}")
        except Exception as exc:
            error_count += 1
            consecutive_errors += 1
            current_interval = min(current_interval * 1.45, MAX_BACKOFF_SECONDS)
            current_quality = clamp(current_quality - 3, MIN_JPEG_QUALITY, MAX_JPEG_QUALITY)
            print("Error al capturar/enviar:", exc)

        if consecutive_errors >= 3:
            # Al encadenar errores, afloja más para no saturar la red.
            current_interval = min(current_interval * 1.15, MAX_BACKOFF_SECONDS)

        now = time.time()
        if now - last_report_at >= STATS_EVERY_SECONDS:
            print(
                f"[stats] sent={sent_count} skipped={skipped_count} errors={error_count} "
                f"q={current_quality} mode={current_mode} size={last_kb:.1f}KB "
                f"rtt={last_rtt_ms:.0f}ms diff={last_diff_score:.2f} interval={current_interval:.2f}s"
            )
            last_report_at = now

        elapsed = time.time() - loop_started
        sleep_for = max(0.0, current_interval - elapsed)
        time.sleep(sleep_for)


if __name__ == "__main__":
    capturar_y_enviar()
