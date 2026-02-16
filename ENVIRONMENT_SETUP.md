# Environment Configuration Guide

**Date:** 2026-02-16  
**Version:** 1.0

---

## Overview

This guide covers environment configuration for the Budtender Feedback System, including development and production setups.

---

## Quick Start

### Development Setup

```bash
# 1. Copy example file
cp .env.example .env

# 2. Generate SECRET_KEY
python generate_secret_key.py

# 3. Edit .env and add the generated key
nano .env

# 4. Start application
python run.py
```

### Production Setup

```bash
# Use interactive wizard
python setup_production_env.py

# Or manually:
cp .env.example .env
nano .env
chmod 600 .env
```

---

## Environment Variables

### Required Variables

#### SECRET_KEY
**Purpose:** Cryptographic key for JWT tokens and session security

**Requirements:**
- Minimum 32 characters
- Cryptographically random
- Never commit to version control

**Generate:**
```bash
python generate_secret_key.py
```

**Example:**
```bash
SECRET_KEY=092c0b2098cf54c4b311703ad2a595dafbdf55addd1fa09acf67f0748968b6bc
```

---

### Environment Configuration

#### ENV
**Purpose:** Application environment mode

**Values:**
- `development` - Auto-generates SECRET_KEY if missing, enables debug features
- `production` - Requires SECRET_KEY, disables debug features

**Default:** `development`

**Example:**
```bash
ENV=production
```

#### DEBUG
**Purpose:** Enable/disable debug mode

**Values:**
- `true` - Detailed error messages, auto-reload, verbose logging
- `false` - Generic error messages, production-ready

**Default:** `true` in development, `false` in production

**Example:**
```bash
DEBUG=false
```

#### LOG_LEVEL
**Purpose:** Logging verbosity

**Values:**
- `DEBUG` - All messages (development)
- `INFO` - General information (production)
- `WARNING` - Warnings and errors only
- `ERROR` - Errors only
- `CRITICAL` - Critical errors only

**Default:** `DEBUG` in development, `INFO` in production

**Example:**
```bash
LOG_LEVEL=INFO
```

---

### OpenAI Configuration

#### OPENAI_API_KEY
**Purpose:** OpenAI API key for AI enrichment pipeline

**Features:**
- Auto-translate feedback to English and Russian
- Generate summaries
- Auto-tag feedback

**Fallback:** If not set, uses keyword-based pipeline

**Get Key:** https://platform.openai.com/api-keys

**Example:**
```bash
OPENAI_API_KEY=sk-proj-...
```

#### OPENAI_MODEL
**Purpose:** OpenAI model to use

**Values:**
- `gpt-4o-mini` - Cost-effective, fast (recommended)
- `gpt-4o` - More capable, slower
- `gpt-4-turbo` - Balanced

**Default:** `gpt-4o-mini`

**Example:**
```bash
OPENAI_MODEL=gpt-4o-mini
```

#### OPENAI_TIMEOUT
**Purpose:** Timeout for OpenAI API requests (seconds)

**Default:** `30`

**Example:**
```bash
OPENAI_TIMEOUT=30
```

---

### Rate Limiting

#### RATE_LIMIT_MAX
**Purpose:** Maximum submissions per IP per time window

**Default:** `10`

**Recommendations:**
- Development: `100` (for testing)
- Production: `10` (prevent spam)
- High-traffic: `20-50`

**Example:**
```bash
RATE_LIMIT_MAX=10
```

#### RATE_LIMIT_WINDOW_HOURS
**Purpose:** Time window for rate limiting (hours)

**Default:** `24`

**Example:**
```bash
RATE_LIMIT_WINDOW_HOURS=24
```

---

### File Upload

#### MAX_FILE_SIZE
**Purpose:** Maximum file upload size in bytes

**Default:** `5242880` (5MB)

**Examples:**
- 5MB: `5242880`
- 10MB: `10485760`
- 20MB: `20971520`

**Example:**
```bash
MAX_FILE_SIZE=5242880
```

#### ALLOWED_EXTENSIONS
**Purpose:** Comma-separated list of allowed file extensions

**Default:** `jpg,jpeg,png`

**Example:**
```bash
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif
```

---

### JWT Configuration

#### ACCESS_TOKEN_EXPIRE_MINUTES
**Purpose:** JWT token expiration time (minutes)

**Default:** `480` (8 hours)

**Recommendations:**
- Short sessions: `60` (1 hour)
- Standard: `480` (8 hours)
- Long sessions: `1440` (24 hours)

**Example:**
```bash
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

---

### Application

#### APP_NAME
**Purpose:** Application name for logging and display

**Default:** `Budtender Feedback System`

**Example:**
```bash
APP_NAME=Budtender Feedback System
```

#### APP_VERSION
**Purpose:** Application version

**Default:** `1.0.0`

**Example:**
```bash
APP_VERSION=1.0.0
```

---

### Security

#### CORS_ORIGINS
**Purpose:** Comma-separated list of allowed CORS origins

**Default:** `*` (all origins - NOT recommended for production)

**Production Example:**
```bash
CORS_ORIGINS=https://joyyfeedback.com,https://www.joyyfeedback.com
```

**Development:**
```bash
CORS_ORIGINS=*
```

#### TRUSTED_HOSTS
**Purpose:** Comma-separated list of trusted host headers

**Default:** `*` (all hosts - NOT recommended for production)

**Production Example:**
```bash
TRUSTED_HOSTS=joyyfeedback.com,www.joyyfeedback.com
```

**Development:**
```bash
TRUSTED_HOSTS=*
```

---

## Configuration Examples

### Development Configuration

```bash
# .env for development
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=auto-generated-if-not-set
OPENAI_API_KEY=sk-...
RATE_LIMIT_MAX=100
CORS_ORIGINS=*
TRUSTED_HOSTS=*
```

### Production Configuration

```bash
# .env for production
ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=092c0b2098cf54c4b311703ad2a595dafbdf55addd1fa09acf67f0748968b6bc
OPENAI_API_KEY=sk-proj-...
RATE_LIMIT_MAX=10
RATE_LIMIT_WINDOW_HOURS=24
MAX_FILE_SIZE=5242880
ALLOWED_EXTENSIONS=jpg,jpeg,png
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=https://joyyfeedback.com,https://www.joyyfeedback.com
TRUSTED_HOSTS=joyyfeedback.com,www.joyyfeedback.com
APP_NAME=Budtender Feedback System
APP_VERSION=1.0.0
```

---

## Setup Scripts

### Interactive Setup Wizard

```bash
python setup_production_env.py
```

**Features:**
- Interactive prompts for all settings
- Auto-generates SECRET_KEY
- Validates input
- Creates backup of existing .env
- Sets secure permissions (600)
- Creates backup in ~/.budtender_backups/

### Manual Setup

```bash
# 1. Copy example
cp .env.example .env

# 2. Generate SECRET_KEY
python generate_secret_key.py

# 3. Edit .env
nano .env

# 4. Set secure permissions
chmod 600 .env

# 5. Test configuration
python test_environment.py
```

---

## Security Best Practices

### File Permissions

```bash
# Set secure permissions (owner read/write only)
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (600)
```

### Version Control

```bash
# Verify .env is in .gitignore
grep "^\.env$" .gitignore

# Check git status (should not show .env)
git status

# If .env is tracked, remove it:
git rm --cached .env
git commit -m "Remove .env from version control"
```

### Backup

```bash
# Create backup in secure location
mkdir -p ~/.budtender_backups
cp .env ~/.budtender_backups/env_backup_$(date +%Y%m%d_%H%M%S)
chmod 600 ~/.budtender_backups/env_backup_*

# List backups
ls -lh ~/.budtender_backups/
```

### Rotation

**Rotate SECRET_KEY periodically:**

```bash
# 1. Generate new key
python generate_secret_key.py

# 2. Update .env with new key
nano .env

# 3. Restart application
docker compose restart

# Note: This will invalidate all existing JWT tokens
```

---

## Testing

### Run Environment Tests

```bash
python test_environment.py
```

**Tests include:**
- ✅ .env file exists
- ✅ .env has secure permissions (600)
- ✅ .env is in .gitignore
- ✅ Config module loads
- ✅ SECRET_KEY is set and valid
- ✅ Environment variables are valid
- ✅ OpenAI configuration
- ✅ Rate limiting configuration
- ✅ File upload configuration
- ✅ JWT configuration
- ✅ Database paths
- ✅ Security configuration
- ✅ Production readiness

### Manual Testing

```bash
# Test config loading
python -c "from app.config import *; print('Config loaded successfully')"

# Check SECRET_KEY length
python -c "from app.config import SECRET_KEY; print(f'SECRET_KEY length: {len(SECRET_KEY)}')"

# Check environment
python -c "from app.config import ENV, DEBUG, LOG_LEVEL; print(f'ENV={ENV}, DEBUG={DEBUG}, LOG_LEVEL={LOG_LEVEL}')"

# Check OpenAI
python -c "from app.config import OPENAI_API_KEY; print('OpenAI:', 'Enabled' if OPENAI_API_KEY else 'Disabled')"
```

---

## Troubleshooting

### SECRET_KEY Too Short

**Error:**
```
ERROR: SECRET_KEY must be at least 32 characters long (current: 16)
```

**Solution:**
```bash
python generate_secret_key.py
# Copy the generated key to .env
```

### SECRET_KEY Missing in Production

**Error:**
```
ERROR: SECRET_KEY must be set in production environment!
```

**Solution:**
```bash
# Set ENV=development for testing, or
# Generate and set SECRET_KEY
python generate_secret_key.py
nano .env
```

### Config Module Won't Load

**Error:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Solution:**
```bash
pip install python-dotenv
```

### .env Not Loading

**Check:**
1. File exists: `ls -la .env`
2. File is in project root
3. python-dotenv installed: `pip list | grep dotenv`
4. No syntax errors in .env

### Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: '.env'
```

**Solution:**
```bash
chmod 600 .env
```

---

## Production Checklist

### Before Deployment

- [ ] Run `python setup_production_env.py`
- [ ] Set `ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Set `LOG_LEVEL=INFO`
- [ ] Generate strong `SECRET_KEY` (32+ chars)
- [ ] Set `OPENAI_API_KEY` (if using AI features)
- [ ] Configure `CORS_ORIGINS` for your domain
- [ ] Configure `TRUSTED_HOSTS` for your domain
- [ ] Set appropriate `RATE_LIMIT_MAX`
- [ ] Set secure file permissions: `chmod 600 .env`
- [ ] Verify `.env` in `.gitignore`
- [ ] Create backup: `cp .env ~/.budtender_backups/`
- [ ] Run tests: `python test_environment.py`

### After Deployment

- [ ] Verify config loads: `docker compose logs | grep "Starting"`
- [ ] Check environment: `docker compose exec bfs python -c "from app.config import ENV; print(ENV)"`
- [ ] Test application: `curl http://localhost:8000/`
- [ ] Monitor logs: `docker compose logs -f`
- [ ] Verify rate limiting works
- [ ] Test file uploads
- [ ] Test admin login

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Prod | Auto-gen | JWT signing key (32+ chars) |
| `ENV` | No | development | Environment mode |
| `DEBUG` | No | Auto | Debug mode |
| `LOG_LEVEL` | No | Auto | Logging verbosity |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `OPENAI_MODEL` | No | gpt-4o-mini | OpenAI model |
| `OPENAI_TIMEOUT` | No | 30 | API timeout (seconds) |
| `RATE_LIMIT_MAX` | No | 10 | Max submissions per IP |
| `RATE_LIMIT_WINDOW_HOURS` | No | 24 | Rate limit window |
| `MAX_FILE_SIZE` | No | 5242880 | Max upload size (bytes) |
| `ALLOWED_EXTENSIONS` | No | jpg,jpeg,png | Allowed file types |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 480 | JWT expiration |
| `APP_NAME` | No | Budtender... | App name |
| `APP_VERSION` | No | 1.0.0 | App version |
| `CORS_ORIGINS` | No | * | CORS origins |
| `TRUSTED_HOSTS` | No | * | Trusted hosts |

---

## Support

For issues or questions:
1. Run tests: `python test_environment.py`
2. Check logs: `docker compose logs`
3. Review this documentation
4. Check `.env.example` for reference

---

**Last Updated:** 2026-02-16  
**Status:** ✅ Production Ready
