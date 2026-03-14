import pyautogui
import base64
import requests
import time
import os
from io import BytesIO

SERVER_URL = os.getenv("SERVER_URL", "https://screen-receiver.onrender.com/upload")


def capturar_y_enviar():
    while True:
        try:
            screenshot = pyautogui.screenshot()
            # En macOS suele venir en RGBA; JPEG requiere RGB.
            if screenshot.mode != "RGB":
                screenshot = screenshot.convert("RGB")
            buffer = BytesIO()
            screenshot.save(buffer, format='JPEG')
            encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')

            requests.post(SERVER_URL, json={'image': encoded})
        except Exception as e:
            print("Error al capturar pantalla:", e)

        time.sleep(1)

if __name__ == "__main__":
    capturar_y_enviar()
