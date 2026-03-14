# MCStation

Captura remota de pantalla con arquitectura simple:

- `sender.py`: captura pantalla en macOS y la envia al receiver.
- `Receiver/receiver.py`: servidor Flask + UI web para ver stream y hacer recorte/copia.

## Requisitos

- macOS con permisos de grabacion de pantalla.
- Python 3.9+.

## Instalacion

```bash
cd /Users/puky/Repositorios/mcstation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-sender.txt
pip install -r Receiver/requirements.txt
```

## Uso rapido

### Sender contra Render

`sender.py` ya viene con default:

- `SERVER_URL=https://macos-sr6q.onrender.com/upload`

Ejecutar:

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
python sender.py
```

Ver en navegador:

- `https://macos-sr6q.onrender.com/`

### Receiver local para pruebas

Terminal 1:

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
PORT=5050 python Receiver/receiver.py
```

Terminal 2:

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
SERVER_URL=http://127.0.0.1:5050/upload python sender.py
```

Abrir:

- `http://127.0.0.1:5050/`

## Variables de entorno (sender)

- `SERVER_URL`: endpoint `/upload`.
- `PROFILE`: `quality` (default), `wifi_balanced`, `low_bandwidth`.
- `TARGET_FPS`: fps objetivo.
- `JPEG_QUALITY`, `MIN_JPEG_QUALITY`, `MAX_JPEG_QUALITY`.
- `MAX_WIDTH`, `MAX_HEIGHT`: limite de resolucion (`0` = sin limite).
- `CHANGE_THRESHOLD`: sensibilidad para omitir frames casi iguales.
- `UPLOAD_MODE`: `auto`, `multipart`, `json`.

Ejemplo alta calidad fija:

```bash
SERVER_URL=https://macos-sr6q.onrender.com/upload \
PROFILE=quality \
MAX_WIDTH=0 \
MAX_HEIGHT=0 \
JPEG_QUALITY=82 \
MIN_JPEG_QUALITY=82 \
MAX_JPEG_QUALITY=82 \
TARGET_FPS=1.0 \
python sender.py
```

## Build de app macOS (sin icono en Dock)

Se usa `ScreenCaptureHelper.spec` con `LSUIElement=true`.

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
pip install pyinstaller
pyinstaller --noconfirm ScreenCaptureHelper.spec
```

Salida:

- `dist/ScreenCaptureHelper.app`

Copiar a aplicaciones del usuario:

```bash
mkdir -p ~/Applications
rsync -a dist/ScreenCaptureHelper.app/ ~/Applications/ScreenCaptureHelper.app/
open ~/Applications/ScreenCaptureHelper.app
```

## Permisos macOS

Si no envia imagen:

1. `Ajustes del Sistema > Privacidad y seguridad > Grabacion de pantalla`.
2. Habilitar la app (`ScreenCaptureHelper` o terminal usada).
3. Cerrar y abrir nuevamente la app/proceso.

## Render (receiver)

Para desplegar desde este repo:

- Root Directory: `Receiver`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python receiver.py`

