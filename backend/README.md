# Help2Mail — Bulk Email Campaign Backend

Production-grade FastAPI backend that lets you upload an Excel/CSV file of
company names + emails, enter a subject & description, attach your resume, and
send personalised job-application emails from your **own Gmail account** — all
from a single form submission.

---

## Features

| Feature | Description |
|---|---|
| **Gmail OAuth2** | Sends from the user's own Gmail — no SMTP, no app passwords |
| **MongoDB + Beanie** | Async MongoDB ODM (Pydantic-native) via Motor driver |
| **Excel / CSV parsing** | Auto-detects email & name columns via fuzzy matching |
| **Background sending** | Emails dispatched async via FastAPI `BackgroundTasks` |
| **Rate limiting** | Configurable per-email delay to stay within Gmail quotas |
| **Campaign tracking** | Real-time status, paginated logs, CSV export |
| **Structured logging** | `structlog` with JSON (prod) / pretty console (dev), email masking |

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- **MongoDB** running locally (default: `mongodb://localhost:27017`)
- A [Google Cloud project](https://console.cloud.google.com/) with the **Gmail API** enabled
- OAuth 2.0 Client ID (Web application type) with `http://localhost:8000/api/v1/auth/callback` as an authorised redirect URI

### 2. Install

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your Google OAuth credentials, MongoDB URL, and a random SECRET_KEY
```

### 4. Run

```bash
uvicorn app.main:app --reload
```

The API is live at **http://localhost:8000**. Interactive docs at **http://localhost:8000/docs**.

---

## API Endpoints

### Auth

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/auth/login` | Get Google OAuth2 login URL |
| `GET` | `/api/v1/auth/callback?code=…` | OAuth2 callback (automatic redirect) |
| `GET` | `/api/v1/auth/me` | Get current logged-in user |
| `POST` | `/api/v1/auth/logout` | Log out (clear session) |

### Campaign

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/campaign/start` | Upload Excel + resume, start campaign |
| `GET` | `/api/v1/campaign/history` | List all campaigns (newest first) |
| `GET` | `/api/v1/campaign/{id}` | Get campaign status + counts |
| `GET` | `/api/v1/campaign/{id}/logs` | Paginated email logs |
| `GET` | `/api/v1/campaign/{id}/export` | Download CSV of all logs |

---

## Running Tests

Tests use **mongomock-motor** — no real MongoDB needed:

```bash
cd backend
pytest tests/ -v
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, middleware, routers
│   ├── config.py             # Pydantic BaseSettings
│   ├── api/
│   │   ├── deps.py           # Auth dependency
│   │   └── routes/
│   │       ├── auth.py       # OAuth2 login / callback / logout
│   │       ├── campaign.py   # POST /campaign/start
│   │       └── status.py     # GET campaign status, logs, export
│   ├── core/
│   │   ├── exceptions.py     # Custom exceptions + handlers
│   │   └── security.py       # OAuth scopes, session keys
│   ├── services/
│   │   ├── excel_parser.py   # Excel/CSV → EmailRecipient list
│   │   ├── email_builder.py  # Plain + HTML body builder
│   │   ├── gmail_client.py   # Gmail API send + token refresh
│   │   └── campaign_runner.py# Background send loop
│   ├── db/
│   │   ├── models.py         # Beanie Document models (MongoDB)
│   │   └── session.py        # Motor client + Beanie init
│   └── utils/
│       ├── validators.py     # Email, PDF, file-size checks
│       ├── rate_limiter.py   # Async sleep + TokenBucket
│       └── logger.py         # structlog config + email masker
├── tests/
│   ├── test_excel_parser.py
│   ├── test_email_builder.py
│   └── test_campaign_runner.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_CLIENT_ID` | — | OAuth2 client ID |
| `GOOGLE_CLIENT_SECRET` | — | OAuth2 client secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/callback` | OAuth2 redirect |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `help2mail` | MongoDB database name |
| `RATE_LIMIT_DELAY_SECONDS` | `3` | Delay between emails (seconds) |
| `MAX_RESUME_SIZE_MB` | `5` | Maximum resume upload size |
| `SECRET_KEY` | — | Session cookie signing key |
| `ENV` | `development` | Set to `production` for JSON logs |

---

## License

MIT
