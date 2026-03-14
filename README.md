# MCStation

Proyecto de captura remota de pantalla con dos componentes:

- `sender`: captura la pantalla en macOS y sube frames al receiver.
- `receiver`: servicio Flask + UI web para ver stream, fullscreen y recorte/copia.

## Estructura

```text
mcstation/
├── assets/
│   └── icons/
│       └── screencapturehelper.icns
├── packaging/
│   └── macos/
│       └── ScreenCaptureHelper.spec
├── receiver/
│   ├── app.py
│   └── requirements.txt
├── scripts/
│   ├── build_macos_app.sh
│   ├── run_receiver_local.sh
│   └── run_sender_local.sh
├── sender/
│   ├── requirements.txt
│   └── sender.py
└── README.md
```

## Requisitos

- macOS
- Python 3.9+

## Instalacion

```bash
cd /Users/puky/Repositorios/mcstation
python3 -m venv .venv
source .venv/bin/activate
pip install -r sender/requirements.txt
pip install -r receiver/requirements.txt
```

## Uso

### Sender contra Render

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
python sender/sender.py
```

Por defecto usa:

- `SERVER_URL=https://macos-sr6q.onrender.com/upload`

### Prueba local completa

Terminal 1:

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
PORT=5050 python receiver/app.py
```

Terminal 2:

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
SERVER_URL=http://127.0.0.1:5050/upload python sender/sender.py
```

Abrir:

- `http://127.0.0.1:5050/`

## Scripts utiles

```bash
./scripts/run_receiver_local.sh
./scripts/run_sender_local.sh
./scripts/build_macos_app.sh
```

## Variables de entorno (sender)

- `SERVER_URL`
- `PROFILE` (`quality`, `wifi_balanced`, `low_bandwidth`)
- `TARGET_FPS`
- `JPEG_QUALITY`, `MIN_JPEG_QUALITY`, `MAX_JPEG_QUALITY`
- `MAX_WIDTH`, `MAX_HEIGHT`
- `CHANGE_THRESHOLD`
- `UPLOAD_MODE` (`auto`, `multipart`, `json`)

## Build app macOS (sin icono en Dock)

```bash
cd /Users/puky/Repositorios/mcstation
source .venv/bin/activate
pip install pyinstaller
pyinstaller --noconfirm packaging/macos/ScreenCaptureHelper.spec
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

1. Ajustes del Sistema > Privacidad y seguridad > Grabacion de pantalla.
2. Habilitar `ScreenCaptureHelper` (o la terminal usada).
3. Cerrar y abrir nuevamente.

## Render (receiver)

Config recomendada:

- Root Directory: `receiver`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`
