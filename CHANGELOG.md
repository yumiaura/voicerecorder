# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Fixed

- Application logs are now written to rotating files inside the mounted
  `./data` volume instead of piling up in the container's Docker JSON log.
  `voicerecorder_worker` had grown a 7.9 GiB `-json.log` while retrying an
  unavailable ALSA capture device. Each entrypoint keeps its own file —
  `data/logs/recorder.log`, `data/logs/api.log`, `data/logs/stt_queue.log` —
  capped at 10 MiB with 5 rotated copies, so the worst case per service is
  60 MiB. Console output is unchanged, so `docker logs` still works.
  Branch: `fix/log-to-project-data-dir`.

### Added

- `LOG_DIR`, `LOG_MAX_BYTES` and `LOG_BACKUP_COUNT` settings in `config.py`
  and `.env.example`. `LOG_DIR` defaults to the `logs` folder next to
  `RECORD_DIR`, which resolves to `/opt/app_data/logs` in the containers and
  to `./data/logs` on the host. Branch: `fix/log-to-project-data-dir`.
