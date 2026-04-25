# Voice recorder (Ubuntu 24.04)

     Ogg  , -    ,  STT. API  UI  Flask + Vue 2 (CDN). : /  env (JWT).

## 

- ** Docker:** Python 3.12, `ffmpeg`, PulseAudio/PipeWire (`pactl`), venv.
- ** Docker:** Docker Engine + Compose v2 ( `docker compose`).

##   ( Docker)

1.         :

   ```bash
   cp .env.example .env
   ```

2.     API:

   ```bash
   python3.12 -m venv .venv
   . .venv/bin/activate
   pip install -r api/requirements.txt
   ```

3.     ( 3  +   `ffplay`):

   ```bash
   chmod +x scripts/mic_select.sh
   ./scripts/mic_select.sh
   ```

    `PULSE_SOURCE`   `.env`.

4.  API  - (  ):

   ```bash
   python3 api/app1.py
   ```

     : `http://127.0.0.1:5000/` —    **admin** / **admin** (. `AUTH_USERNAME`  `AUTH_PASSWORD`  `.env`).

5.   ( , venv ):

   ```bash
   python3 recorder/record.py
   ```

6.  STT ( `STT_ENABLED=1`  `.env`):

   ```bash
   python3 worker/stt_queue.py
   ```

7.  UI  dev-   3000:

   ```bash
   cd www && npm install && node server.js
   ```

    `http://127.0.0.1:3000/` (  API `:5000`).     ,      Flask.

## Docker Compose

   [Dockerfile](Dockerfile)   ,   `./data`:

```bash
cp .env.example .env
#         compose (. docker-compose.yml).
docker compose build
docker compose up -d
```

UI  API: `http://127.0.0.1:5000/`.

###  «pull access denied for voicerecorder_api»

Compose     ****   registry,     .  [docker-compose.yml](docker-compose.yml)   `app_api`  **`pull_policy: build`**:   ,   `Dockerfile`,  `docker pull`.

   Compose   `pull_policy`,     :

```bash
docker compose build --no-cache app_api
docker compose up -d
```

##  

. [.env.example](.env.example). :

|  |  |
|------------|------------|
| `AUTH_USERNAME`, `AUTH_PASSWORD` |   (  `admin` / `admin`) |
| `SECRET_KEY` |  JWT   Flask;        |
| `AUTH_JWT_HOURS` |   JWT () |
| `RECORD_DIR`, `SEGMENT_MINUTES`, `PULSE_SOURCE` |  |
| `SQLITE_PATH` |  SQLite |
| `STT_ENABLED`, `STT_URL` |  STT HTTP API |

## API ()

- `POST /api/auth/login` — JSON `{"username","password"}` → `access_token`.
-  `GET /api/*` —  `Authorization: Bearer <token>`.
- `GET /api/stream/<id>?access_token=<token>` —   `<audio>` (query  ).

## 

- `api/` — Flask,  Peewee, JWT.
- `recorder/record.py` —    ffmpeg.
- `worker/stt_queue.py` —  .
- `www/src/` — Vue 2 + Bootstrap ( ).
