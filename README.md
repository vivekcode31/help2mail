# ✉️ Help2Mail

> **Bulk Email Campaign Manager** — Send personalized job applications from your Gmail account with a single form submission...

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb?style=flat-square&logo=react&logoColor=white)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7+-47a248?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)](#)

</div>

---

## 🚀 Features

- **🔐 Gmail OAuth2** — Send emails from your own Gmail account securely
- **📊 Excel/CSV Support** — Auto-detect email and name columns via fuzzy matching
- **⚡ Async Processing** — Background email delivery with real-time status tracking
- **⏱️ Rate Limiting** — Configurable delays to respect Gmail quotas
- **📈 Campaign Analytics** — Track sent/failed emails with detailed logs
- **💾 Export Functionality** — Download campaign logs as CSV
- **🗄️ MongoDB + Beanie** — Type-safe async MongoDB with Pydantic models
- **📝 Structured Logging** — JSON logs in production, pretty console in development
- **🔒 Email Masking** — Sensitive data masked in logs for privacy

---

## 📋 Quick Start

### Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **MongoDB** — [Install locally](https://www.mongodb.com/docs/manual/installation/) or use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- **Google Cloud Project** — [Create one](https://console.cloud.google.com/) and enable Gmail API
- **OAuth 2.0 Credentials** — Web application type with redirect URI: `http://localhost:8000/api/v1/auth/callback`

### Installation

#### 1️⃣ Clone the repository

```bash
git clone https://github.com/vivekcode31/help2mail.git
cd help2mail
```

#### 2️⃣ Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3️⃣ Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Google OAuth2
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=help2mail

# Server Configuration
SECRET_KEY=your_random_secret_key_here
ENV=development

# Rate Limiting
RATE_LIMIT_DELAY_SECONDS=3
MAX_RESUME_SIZE_MB=5
```

#### 4️⃣ Run Backend

```bash
uvicorn app.main:app --reload
```

✅ Backend is live at **[http://localhost:8000](http://localhost:8000)**  
📖 Interactive API Docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

#### 5️⃣ Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ Frontend is live at **[http://localhost:5173](http://localhost:5173)**

---

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/auth/login` | Get Google OAuth2 login URL |
| `GET` | `/api/v1/auth/callback` | OAuth2 callback (automatic redirect) |
| `GET` | `/api/v1/auth/me` | Get current logged-in user |
| `POST` | `/api/v1/auth/logout` | Log out (clear session) |

### Campaign Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/campaign/start` | Upload Excel + resume, start campaign |
| `GET` | `/api/v1/campaign/history` | List all campaigns (newest first) |
| `GET` | `/api/v1/campaign/{id}` | Get campaign status + counts |
| `GET` | `/api/v1/campaign/{id}/logs` | Paginated email logs |
| `GET` | `/api/v1/campaign/{id}/export` | Download CSV of all logs |

---

## 🧪 Testing

Run tests with **mongomock-motor** (no real MongoDB required):

```bash
cd backend
pytest tests/ -v
```

For coverage report:

```bash
pytest tests/ --cov=app --cov-report=html
```

---

## 🗂️ Project Structure

```
help2mail/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app & middleware
│   │   ├── config.py                # Settings management
│   │   ├── api/
│   │   │   ├── deps.py              # Dependency injection
│   │   │   └── routes/
│   │   │       ├── auth.py          # OAuth2 login/callback/logout
│   │   │       ├── campaign.py      # Campaign endpoints
│   │   │       └── status.py        # Status & tracking
│   │   ├── core/
│   │   │   ├── exceptions.py        # Custom exceptions
│   │   │   └── security.py          # OAuth & session config
│   │   ├── services/
│   │   │   ├── excel_parser.py      # CSV/Excel parsing
│   │   │   ├── email_builder.py     # Email composition
│   │   │   ├── gmail_client.py      # Gmail API wrapper
│   │   │   └── campaign_runner.py   # Background tasks
│   │   ├── db/
│   │   │   ├── models.py            # MongoDB schemas
│   │   │   └── session.py           # DB connection
│   │   └── utils/
│   │       ├── validators.py        # Data validation
│   │       ├── rate_limiter.py      # Rate limiting
│   │       └── logger.py            # Structured logging
│   ├── tests/
│   │   ├── test_excel_parser.py
│   │   ├── test_email_builder.py
│   │   └── test_campaign_runner.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
└── frontend/                         # React + TypeScript + Vite
    ├── src/
    │   ├── components/              # React components
    │   ├── pages/                   # Page components
    │   ├── api/                     # API client
    │   ├── hooks/                   # Custom hooks
    │   └── App.tsx
    ├── public/
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | — | OAuth2 Client ID |
| `GOOGLE_CLIENT_SECRET` | — | OAuth2 Client Secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/callback` | OAuth2 Redirect URL |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB Connection String |
| `MONGODB_DB_NAME` | `help2mail` | Database Name |
| `RATE_LIMIT_DELAY_SECONDS` | `3` | Delay between emails (seconds) |
| `MAX_RESUME_SIZE_MB` | `5` | Maximum resume file size |
| `SECRET_KEY` | — | Session signing key |
| `ENV` | `development` | Set to `production` for JSON logs |

---

## 🔄 Workflow Diagram

```
User Login (OAuth2)
      ↓
Upload CSV/Excel + Resume
      ↓
Parse Recipients (auto-detect columns)
      ↓
Validate & Clean Data
      ↓
Create Email Queue
      ↓
Apply Rate Limiting
      ↓
Send via Gmail API
      ↓
Log Results & Update Status
      ↓
Display Analytics Dashboard
      ↓
Export Campaign Reports
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** your feature branch:
   ```bash
git checkout -b feature/AmazingFeature
```
3. **Commit** your changes:
   ```bash
git commit -m '✨ Add AmazingFeature'
```
4. **Push** to the branch:
   ```bash
git push origin feature/AmazingFeature
```
5. **Open** a Pull Request

---

## 🐛 Troubleshooting

### MongoDB Connection Issues
```bash
# Make sure MongoDB is running
mongod

# Or use MongoDB Atlas cloud
# Update MONGODB_URL in .env
```

### Gmail API Errors
- Verify Client ID and Secret in `.env`
- Check redirect URI matches Google Cloud Console
- Ensure Gmail API is enabled in your project

### Port Already in Use
```bash
# Change backend port
uvicorn app.main:app --reload --port 8001

# Change frontend port in vite.config.ts
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 💡 Support

Need help? Here are your options:

- 📖 Check the [API Documentation](http://localhost:8000/docs)
- 🐛 Open an [Issue](https://github.com/vivekcode31/help2mail/issues)
- 💬 Start a [Discussion](https://github.com/vivekcode31/help2mail/discussions)
- 📧 Contact: vivekvipar18@gmail.com

---

<div align="center">

⭐ **If you find this project useful, please star it!**

Made with ❤️ by [vivekcode31](https://github.com/vivekcode31)

</div>
