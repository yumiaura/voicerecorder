# Voice recorder (Ubuntu 24.04)

Local microphone recording to segmented Ogg files, web playback with time jumps, optional STT. API and UI are built with Flask + Vue 2 (CDN). Auth: username/password from env (JWT).

## Requirements

- **Without Docker:** Python 3.12, `ffmpeg`, PulseAudio/PipeWire (`pactl`), venv.
- **With Docker:** Docker Engine + Compose v2 (`docker compose` plugin).

## Quick Start (without Docker)

1. Copy env file and edit paths/passwords if needed:

   ```bash
   cp .env.example .env
   ```

2. Create virtualenv and install API dependencies:

   ```bash
   python3.12 -m venv .venv
   . .venv/bin/activate
   pip install -r api/requirements.txt
   ```

3. Select and test microphone (3s record + playback via `ffplay`):

   ```bash
   chmod +x scripts/mic_select.sh
   ./scripts/mic_select.sh
   ```

   Put the resulting `PULSE_SOURCE` value into `.env`.

4. Start API and web UI (from repository root):

   ```bash
   python3 api/app1.py
   ```

   Open: `http://127.0.0.1:5000/` — default login is **admin** / **admin** (see `AUTH_USERNAME` and `AUTH_PASSWORD` in `.env`).

5. Start recording segments (separate terminal, venv active):

   ```bash
   python3 recorder/record.py
   ```

6. Start STT queue (if `STT_ENABLED=1` in `.env`):

   ```bash
   python3 worker/stt_queue.py
   ```

7. Optional UI via dev proxy on port 3000:

   ```bash
   cd www && npm install && node server.js
   ```

   Open `http://127.0.0.1:3000/` (proxying API `:5000`). Token and headers are the same as direct Flask usage.

## Docker Compose

Now three containers are started:
- `voicerecorder_api` — Flask API
- `voicerecorder_www` — frontend (Node/Express proxy), runs separately and executes `npm install && node server.js` on startup
- `voicerecorder_worker` — separate microphone recording process (`recorder/record.py`)

Build/run:

```bash
cp .env.example .env
docker compose build
docker compose up -d
```

UI: `http://127.0.0.1:${WWW_PORT}` (default `5011`)  
API: `http://127.0.0.1:${API_PORT}` (default `5010`)  
Inside docker network, services listen on the same ports: API `5010`, WWW `5011`.

Recorder logs:

```bash
docker compose logs -f voicerecorder_worker
```

Expected log lines:
- `START segment file=...`
- `FINISH segment ok file=...`
- `FINISH segment failed file=...`

For hosts without working Pulse, use ALSA (recommended for your USB mic `card 2, device 0`):

```env
RECORDER_INPUT=alsa
ALSA_DEVICE=plughw:2,0
RECORDER_CHANNELS=1
```

If you see `Error opening input file default` in `voicerecorder_worker`:

1. For ALSA: set `RECORDER_INPUT=alsa` and `ALSA_DEVICE=plughw:2,0`.
2. For Pulse: set proper source from `scripts/mic_select.sh` in `.env`:
   - `PULSE_SOURCE=<your_source_name>`
3. Check Pulse access for container:
   - `PULSE_SOCKET=/run/user/<uid>/pulse/native`
   - `PULSE_COOKIE=/home/<user>/.config/pulse/cookie`
   - `LOCAL_UID=<uid>`, `LOCAL_GID=<gid>`
4. Restart worker:
   - `docker compose up -d --build voicerecorder_worker`

### "pull access denied for voicerecorder_api"

By default Compose may try to **pull** an image from registry when no local tag exists. In [docker-compose.yml](docker-compose.yml), services use **`pull_policy: build`**, so only locally built images are used.

If your Compose version does not support `pull_policy`, run explicit build + up:

```bash
docker compose build --no-cache voicerecorder_api voicerecorder_www
docker compose up -d
```

## Environment Variables

See [.env.example](.env.example). Key values:

| Variable | Purpose |
|----------|---------|
| `AUTH_USERNAME`, `AUTH_PASSWORD` | Local login (default `admin` / `admin`) |
| `SECRET_KEY` | JWT and Flask session signing key; set a long random string outside local testing |
| `AUTH_JWT_HOURS` | JWT lifetime in hours |
| `RECORD_DIR`, `SEGMENT_MINUTES`, `PULSE_SOURCE` | Recording settings |
| `PULSE_SOCKET` | Host PulseAudio socket path used by `voicerecorder_worker` |
| `SQLITE_PATH` | SQLite database path |
| `STT_ENABLED`, `STT_URL` | External STT HTTP API |

## API (short)

- `POST /api/auth/login` — JSON `{"username","password"}` -> `access_token`.
- Other `GET /api/*` — require `Authorization: Bearer <token>` header.
- `GET /api/stream/<id>?access_token=<token>` — for `<audio>` element (query token instead of header).

## Structure

- `api/` — Flask, Peewee models, JWT.
- `recorder/record.py` — ffmpeg recording loop.
- `worker/stt_queue.py` — transcription queue.
- `www/src/` — Vue 2 + Bootstrap (no build step).
