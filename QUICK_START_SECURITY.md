# Quick Start - Security Setup

## 🔐 Before First Run

### 1. Generate Secure SECRET_KEY

```bash
python generate_secret_key.py
```

This will output 3 options. Copy one of them (Option 1 recommended).

### 2. Create .env File

```bash
cp .env.example .env
```

### 3. Edit .env File

Open `.env` and add your generated key:

```bash
# REQUIRED: Set this to a key from generate_secret_key.py
SECRET_KEY=092c0b2098cf54c4b311703ad2a595dafbdf55addd1fa09acf67f0748968b6bc

# OPTIONAL: Add OpenAI key if you have one
OPENAI_API_KEY=sk-your-key-here

# Set to production when deploying
ENV=development
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Application

```bash
python run.py
```

---

## ✅ What's New

### Security Improvements
- ✅ All dependencies updated to latest secure versions
- ✅ 3 critical CVEs patched (python-jose, jinja2)
- ✅ SECRET_KEY validation on startup
- ✅ Production mode enforcement

### New Tools
- `generate_secret_key.py` - Generate cryptographically secure keys
- `SECURITY_AUDIT.md` - Complete security audit report
- `CHANGELOG.md` - All changes documented

### New Dependencies
- `python-dotenv` - Proper .env file handling
- `python-magic` - MIME type validation (to be implemented)

---

## 🚨 Production Deployment

Before deploying to production:

1. **Set ENV=production in .env**
   ```bash
   ENV=production
   ```

2. **Generate and set a strong SECRET_KEY**
   ```bash
   python generate_secret_key.py
   # Copy to .env
   ```

3. **Change default passwords**
   - admin@weeden.com
   - founder@weeden.com
   - ceo@weeden.com

4. **Configure HTTPS/SSL**
   - Use Nginx reverse proxy
   - Install SSL certificate with Certbot

5. **Set up backups**
   - Database: `data/budtender.db`
   - Uploads: `data/uploads/`

---

## 🔍 Verify Security

### Check Dependencies
```bash
pip install safety
safety check -r requirements.txt
```

Expected: ✅ No known vulnerabilities

### Test SECRET_KEY Validation
```bash
# Should fail (key too short)
SECRET_KEY=short python run.py

# Should fail in production (no key)
ENV=production python run.py

# Should work
SECRET_KEY=your-32-char-or-longer-key-here python run.py
```

---

## 📚 Documentation

- `SECURITY_AUDIT.md` - Security audit results
- `DEPLOYMENT_TODO.md` - Complete deployment checklist
- `CHANGELOG.md` - All changes
- `README.md` - General documentation

---

## ❓ Troubleshooting

### "ERROR: SECRET_KEY must be set in production environment!"
**Solution:** Set SECRET_KEY in .env file or environment variable

### "ERROR: SECRET_KEY must be at least 32 characters long"
**Solution:** Use `python generate_secret_key.py` to generate a proper key

### "WARNING: Using auto-generated SECRET_KEY"
**Solution:** This is OK for development, but set a permanent key in .env

---

**Status:** ✅ Ready for testing  
**Next:** Follow DEPLOYMENT_TODO.md for full deployment
