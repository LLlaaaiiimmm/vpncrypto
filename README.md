# Budtender Feedback System (BFS)

Anonymous employee feedback system for Weeden cannabis retail chain.
Two-part architecture: **public anonymous form** (Joy Monkey) + **admin dashboard** with AI enrichment.

---

## Quick Start

### Option A: Local (Python 3.9+)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set OpenAI key for AI translations
export OPENAI_API_KEY=sk-...

# 3. Run
python run.py
```

### Option B: Docker

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your SECRET_KEY and optional OPENAI_API_KEY

# 2. Build & run
docker compose up --build -d
```

The system starts at **http://localhost:8000**

---

## Demo Accounts

| Role    | Email                | Password        | Permissions                       |
|---------|----------------------|-----------------|-----------------------------------|
| Admin   | admin@weeden.com     | admin12345!     | Full access + user mgmt + delete  |
| Founder | founder@weeden.com   | founder12345    | Inbox, analytics, export, notes   |
| CEO     | ceo@weeden.com       | ceo1234567!     | Inbox, analytics, export, notes   |

> Change these passwords immediately in production.

---

## URLs

| Page              | URL                              | Access        |
|-------------------|----------------------------------|---------------|
| Public Form       | http://localhost:8000/            | Anyone        |
| Admin Login       | http://localhost:8000/admin/login | Auth required |
| Inbox             | http://localhost:8000/admin/inbox | Auth required |
| Feedback Detail   | http://localhost:8000/admin/feedback/{id} | Auth required |
| Analytics         | http://localhost:8000/admin/analytics | Auth required |
| User Management   | http://localhost:8000/admin/users | Admin only    |
| CSV Export         | http://localhost:8000/admin/export | Auth required |

---

## Architecture

```
Budtender System/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration & environment variables
│   ├── database.py         # SQLite schema & connection
│   ├── auth.py             # JWT auth, bcrypt passwords, RBAC
│   ├── ai_pipeline.py      # OpenAI GPT-4o-mini or fallback pipeline
│   ├── main.py             # FastAPI routes (public form, admin, API)
│   ├── static/
│   │   └── css/style.css   # Full responsive CSS
│   └── templates/
│       ├── public/         # form.html, thank_you.html, rate_limited.html
│       └── admin/          # login, inbox, detail, analytics, users, _sidebar
├── data/                   # Auto-created: SQLite DB + uploaded photos
│   ├── budtender.db
│   └── uploads/
├── seed_data.py            # 12 realistic demo feedback entries
├── run.py                  # Entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Features (per BRD)

### Public Form (Mobile-First)
- Joy Monkey branding with green gradient design
- Category selector: Complaint, Idea, Recommendation, Other
- Free-text message (max 1000 chars, any language)
- Photo upload (JPG/PNG, max 5MB)
- Anonymity consent checkbox (required)
- Submission ID displayed on success (format: WDN-XXX-XX)
- Rate limiting: 10 submissions per IP per 24h
- IP stored as SHA-256 hash (not raw)

### AI Enrichment Pipeline
- **With OpenAI key**: GPT-4o-mini translates to EN + RU, generates 1-2 sentence summary, assigns 1-3 tags from a fixed list of 15
- **Without key**: Keyword-based fallback with language detection and heuristic tagging
- Async processing (non-blocking)
- Tags: Salary, Store, Product, Conflict, Legal, Management, Schedule, Safety, Training, Equipment, Customer, Policy, Communication, Hygiene, Other

### Admin Dashboard
- JWT auth with httpOnly cookies (8h TTL)
- RBAC: Admin (full), Founder (read/manage), CEO (read/manage)
- **Inbox**: sortable table, status badges, AI summary preview, tag chips, photo indicator
- **Filters**: by status, category, tag + full-text search
- **Bulk actions**: select multiple & change status
- **Detail view**: original message, EN/RU translations, AI summary, tags, status dropdown, private notes
- **Pagination**: 20 items/page
- **Auto-read**: opening a "new" item marks it as "read"

### User Management (Admin only)
- Create/disable/delete users
- Role assignment: admin, founder, ceo
- Password minimum 10 characters

### Analytics
- Breakdown by category (bar chart)
- Breakdown by status (bar chart)
- Top tags/topics (bar chart)
- Daily volume (last 30 days)

### CSV Export
- Full data export with all fields
- UTF-8 BOM encoding for Excel compatibility

---

## Environment Variables

| Variable         | Required | Default        | Description                        |
|------------------|----------|----------------|------------------------------------|
| SECRET_KEY       | Prod     | Auto-generated | JWT signing key (set in prod!)     |
| OPENAI_API_KEY   | No       | (empty)        | Enables GPT-4o-mini AI pipeline    |
| RATE_LIMIT_MAX   | No       | 10             | Max submissions per IP per 24h     |

---

## Production Deployment Notes

1. **Set a strong SECRET_KEY** in `.env` (min 32 random characters)
2. **Change default passwords** for admin, founder, CEO accounts
3. **HTTPS**: Put behind nginx/Caddy reverse proxy with TLS
4. **Database**: SQLite is fine for <100k records; for scale, migrate to PostgreSQL
5. **File storage**: For multi-server, move uploads to S3/GCS
6. **Backups**: Schedule `data/budtender.db` backups
7. **Domain**: Point your domain to the server, update nginx config

---

## API Endpoints (for integrations)

| Method | Endpoint                           | Description              |
|--------|------------------------------------|--------------------------|
| POST   | /submit                            | Submit anonymous feedback|
| POST   | /api/feedback/{id}/status          | Update status            |
| POST   | /api/feedback/{id}/note            | Save private note        |
| POST   | /api/feedback/bulk-status          | Bulk status update       |
| POST   | /api/feedback/{id}/delete          | Soft delete (admin only) |
| POST   | /api/users                         | Create user (admin only) |
| POST   | /api/users/{id}/toggle             | Enable/disable user      |
| POST   | /api/users/{id}/delete             | Delete user (admin only) |
| GET    | /admin/export                      | CSV export               |

---

## Tech Stack

- **Backend**: Python 3.9+, FastAPI 0.104, Uvicorn
- **Database**: SQLite with WAL mode
- **Auth**: JWT (python-jose), bcrypt (passlib)
- **AI**: OpenAI GPT-4o-mini (optional, with fallback)
- **Frontend**: Jinja2 templates, vanilla CSS/JS
- **Containerization**: Docker, docker-compose
# vpncrypto
