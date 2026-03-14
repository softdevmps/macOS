# macOS

Proyecto de captura remota de pantalla con:

- `sender`: captura y envia frames.
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

## Empezar rapido (local)

Terminal 1:

```bash
source .venv/bin/activate
PORT=5050 python receiver/app.py
```

Terminal 2:

```bash
source .venv/bin/activate
SERVER_URL=http://127.0.0.1:5050/upload python sender/sender.py
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

## Permiso en macOS

Si no se ve imagen, habilitar grabacion de pantalla para la app/terminal en:

- Ajustes del Sistema > Privacidad y seguridad > Grabacion de pantalla.
