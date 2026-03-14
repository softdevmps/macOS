# macOS

Proyecto de captura remota de pantalla con dos componentes:

- `sender`: captura la pantalla y envia frames.
- `receiver`: recibe y muestra frames en web.

## Requisitos

- Python 3.9+
- macOS (para usar `sender`)

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r sender/requirements.txt
pip install -r receiver/requirements.txt
```

## Ejecucion local (rapido)

Terminal 1:

```bash
./scripts/run_receiver_local.sh
```

Terminal 2:

```bash
./scripts/run_sender_local.sh
```

Abrir en navegador:

- `http://127.0.0.1:5050/`

## Usar sender contra receiver remoto

```bash
source .venv/bin/activate
SERVER_URL=https://TU-RECEIVER/upload python sender/sender.py
```

Luego abrir:

- `https://TU-RECEIVER/`

## Build de la app macOS

```bash
./scripts/build_macos_app.sh
```

Salida:

- `dist/macOS.app`

Abrir la app:

```bash
open dist/macOS.app
```

## Permisos en macOS

Si no se ve imagen, habilitar grabacion de pantalla para la app/terminal en:

- Ajustes del Sistema > Privacidad y seguridad > Grabacion de pantalla.
