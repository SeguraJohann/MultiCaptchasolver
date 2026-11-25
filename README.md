# MultiCaptchasolver

HTTP service that solves captchas locally with Python and Playwright.

| Type | Status |
|---|---|
| `recaptcha_v2` (checkbox, audio) | Working |
| `hcaptcha` | Planned, see [docs/hcaptcha.md](docs/hcaptcha.md) |
| reCAPTCHA v3, Amazon WAF | Future |

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
playwright install chromium
python -m multicaptcha --port 8000
```

Configuration: copy `.env.example` to `.env`. Set `API_KEY` before exposing the
service (clients then send `X-API-Key`). The browser is visible by default because
reCAPTCHA blocked audio in headless mode; on a Linux server run it under Xvfb.

## API

`POST /solve` (`GET /health` for liveness)

```json
{
  "type": "recaptcha_v2",
  "url": "https://example.com/form",
  "sitekey": "...",
  "transcriber": "whisper",
  "proxy": {"server": "http://host:port", "username": "u", "password": "p"}
}
```

`transcriber` (default `whisper`) and `proxy` are optional.

Success: `{"status": "ok", "type": ..., "token": ..., "elapsed_seconds": ...}`.
Solver failure: `{"status": "error", "code": ..., "message": ...}` with codes:

| Code | HTTP |
|---|---|
| `invalid_sitekey` | 422 |
| `challenge_blocked` | 503 |
| `timeout` | 504 |
| `attempts_exhausted`, `transcription_failed`, `solver_error` | 502 |

Malformed requests get FastAPI's standard 422 body.

## Structure

```
src/multicaptcha/
  api/           HTTP layer
  core/          models, errors, SolveService (dispatch, concurrency, timeout)
  browser/       Chromium lifecycle, widget page
  transcribers/  Transcriber interface, Whisper, registry
  solvers/       CaptchaSolver interface, registry, one package per captcha type
demo/            end-to-end demo
tests/           unit tests (no network)
```

**New transcriber:** subclass `Transcriber`, add a `TranscriberName`, register it in
`transcribers/registry.py`.

**New captcha:** add a package in `solvers/`, a request model in `core/models.py`,
and register it in `solvers/registry.py`.

## Demo and tests

```bash
python -m demo      # needs the server running
pytest
```
