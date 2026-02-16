import hashlib
import os
import random
import string
import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import sqlite3
import logging

# Configure logging
logger = logging.getLogger(__name__)

from app.config import (
    SECRET_KEY, RATE_LIMIT_MAX, MAX_FILE_SIZE, UPLOAD_DIR, ALLOWED_TAGS
)
from app.database import init_db, get_db
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role
)
from app.ai_pipeline import process_feedback_async
from app.background_tasks import start_cleanup_scheduler, cleanup_old_rate_limits

app = FastAPI(title="Budtender Feedback System")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")
app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "data", "uploads")), name="uploads")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))


# ==================== GLOBAL EXCEPTION HANDLERS ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions (404, 403, etc.)"""
    if exc.status_code == 404:
        # Check if it's an API request or web request
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"detail": "Resource not found"}
            )
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request},
            status_code=404
        )
    elif exc.status_code == 403:
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=403,
                content={"detail": exc.detail or "Access forbidden"}
            )
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "detail": exc.detail},
            status_code=403
        )
    else:
        # For other HTTP errors, return JSON or generic error page
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        return templates.TemplateResponse(
            "errors/error.html",
            {"request": request, "status_code": exc.status_code, "detail": exc.detail},
            status_code=exc.status_code
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors (422)"""
    logger.warning(f"Validation error: {exc.errors()}")
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )
    return templates.TemplateResponse(
        "errors/error.html",
        {"request": request, "status_code": 422, "detail": "Invalid request data"},
        status_code=422
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions (500)"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500
    )


@app.on_event("startup")
def startup():
    init_db()
    _seed_admin()
    # Start background cleanup scheduler (runs every hour)
    start_cleanup_scheduler(interval_hours=1)
    # Run initial cleanup
    cleanup_old_rate_limits()
    logger.info("Application startup complete")


def _seed_admin():
    """Create default admin if no users exist."""
    db = sqlite3.connect(os.path.join(BASE_DIR, "data", "budtender.db"))
    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        db.execute(
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("admin@weeden.com", hash_password("admin12345!"), "System Admin", "admin")
        )
        db.execute(
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("founder@weeden.com", hash_password("founder12345"), "Founder", "founder")
        )
        db.execute(
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("ceo@weeden.com", hash_password("ceo1234567!"), "CEO", "ceo")
        )
        db.commit()
    db.close()


def _hash_ip(ip: str) -> str:
    salt = SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()


def _generate_submission_id() -> str:
    nums = ''.join(random.choices(string.digits, k=3))
    nums2 = ''.join(random.choices(string.digits, k=2))
    return f"WDN-{nums}-{nums2}"


def _validate_image_signature(content: bytes) -> bool:
    """
    Validate image file by checking magic bytes (file signature).
    Returns True if file is a valid JPEG or PNG image.
    """
    if len(content) < 12:
        return False
    
    # JPEG signatures
    # FF D8 FF (JPEG/JFIF)
    if content[:3] == b'\xff\xd8\xff':
        return True
    
    # PNG signature
    # 89 50 4E 47 0D 0A 1A 0A
    if content[:8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
        return True
    
    return False


def _check_rate_limit(db: sqlite3.Connection, ip_hash: str) -> bool:
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    count = db.execute(
        "SELECT COUNT(*) FROM rate_limits WHERE ip_hash = ? AND submitted_at > ?",
        (ip_hash, cutoff)
    ).fetchone()[0]
    return count < RATE_LIMIT_MAX


# ==================== PUBLIC FORM ====================

@app.get("/", response_class=HTMLResponse)
async def public_form(request: Request):
    return templates.TemplateResponse("public/form.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    db: sqlite3.Connection = Depends(get_db)
):
    form = await request.form()
    category = form.get("category", "")
    message = form.get("message", "")
    anonymity_consent = form.get("anonymity_consent", "")
    photo = form.get("photo")

    # Validate consent
    if not anonymity_consent:
        raise HTTPException(status_code=400, detail="Consent required")

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = _hash_ip(client_ip)

    if not _check_rate_limit(db, ip_hash):
        return templates.TemplateResponse("public/rate_limited.html", {"request": request})

    # Validate category
    if category not in ("complaint", "idea", "recommendation", "other"):
        raise HTTPException(status_code=400, detail="Invalid category")

    # Validate message
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if len(message) > 1000:
        raise HTTPException(status_code=400, detail="Message too long (max 1000 characters)")
    
    # Sanitize message - escape HTML to prevent XSS
    # Note: Jinja2 auto-escapes by default, but we sanitize here for extra safety
    import html
    message = html.escape(message.strip())

    # Validate and process photo upload
    photo_path = None
    if photo and hasattr(photo, "filename") and photo.filename:
        content = await photo.read()
        
        # Check file size
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")

        # Validate file extension
        ext = photo.filename.rsplit(".", 1)[-1].lower() if "." in photo.filename else ""
        if ext not in ("jpg", "jpeg", "png"):
            raise HTTPException(status_code=400, detail="Only JPG/PNG images allowed")

        # Validate MIME type using python-magic
        try:
            import magic
            mime = magic.from_buffer(content, mime=True)
            allowed_mimes = ["image/jpeg", "image/png"]
            
            if mime not in allowed_mimes:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type. Only JPEG and PNG images allowed (detected: {mime})"
                )
        except ImportError:
            # Fallback if python-magic not available
            # Check file signature (magic bytes)
            if not _validate_image_signature(content):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file. File signature check failed"
                )

        # Generate safe filename (no user input in filename)
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Write file
        with open(filepath, "wb") as f:
            f.write(content)
        photo_path = filename

    # Generate unique submission ID
    submission_id = _generate_submission_id()
    while db.execute("SELECT 1 FROM feedback WHERE submission_id = ?", (submission_id,)).fetchone():
        submission_id = _generate_submission_id()

    user_agent = request.headers.get("user-agent", "")[:500]

    # Insert feedback
    db.execute("""
        INSERT INTO feedback (submission_id, category, message, photo_path, ip_hash, user_agent)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (submission_id, category, message, photo_path, ip_hash, user_agent))

    db.execute("INSERT INTO rate_limits (ip_hash) VALUES (?)", (ip_hash,))
    db.commit()

    feedback_id = db.execute("SELECT id FROM feedback WHERE submission_id = ?", (submission_id,)).fetchone()[0]
    process_feedback_async(feedback_id)

    return templates.TemplateResponse("public/thank_you.html", {
        "request": request,
        "submission_id": submission_id
    })


# ==================== AUTH ====================

@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = Query(None)):
    """
    Login page with error message support.
    Error codes: no_token, invalid_token, token_expired, user_inactive
    """
    error_messages = {
        "no_token": "Please log in to continue",
        "invalid_token": "Invalid session. Please log in again",
        "token_expired": "Your session has expired. Please log in again",
        "user_inactive": "Your account has been deactivated. Contact administrator",
    }
    error_message = error_messages.get(error) if error else None
    return templates.TemplateResponse("admin/login.html", {
        "request": request, 
        "error": error_message
    })


@app.post("/admin/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db)
):
    user = db.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("admin/login.html", {
            "request": request, "error": "Invalid email or password"
        })

    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    response = RedirectResponse("/admin/inbox", status_code=302)
    response.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=28800)
    return response


@app.get("/admin/logout")
async def logout():
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ==================== ADMIN DASHBOARD ====================

@app.get("/admin/inbox", response_class=HTMLResponse)
async def admin_inbox(
    request: Request,
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    where = ["is_deleted = 0"]
    params = []

    if status:
        where.append("status = ?")
        params.append(status)
    if category:
        where.append("category = ?")
        params.append(category)
    if tag:
        where.append("tags LIKE ?")
        params.append(f"%{tag}%")
    if search:
        where.append("(message LIKE ? OR translation_en LIKE ? OR translation_ru LIKE ? OR summary LIKE ? OR submission_id LIKE ?)")
        s = f"%{search}%"
        params.extend([s, s, s, s, s])

    where_clause = " AND ".join(where)
    total = db.execute(f"SELECT COUNT(*) FROM feedback WHERE {where_clause}", params).fetchone()[0]

    offset = (page - 1) * per_page
    rows = db.execute(
        f"SELECT * FROM feedback WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()

    feedbacks = [dict(r) for r in rows]
    total_pages = max(1, (total + per_page - 1) // per_page)

    stats = {
        "total": db.execute("SELECT COUNT(*) FROM feedback WHERE is_deleted = 0").fetchone()[0],
        "new": db.execute("SELECT COUNT(*) FROM feedback WHERE status = 'new' AND is_deleted = 0").fetchone()[0],
        "read": db.execute("SELECT COUNT(*) FROM feedback WHERE status = 'read' AND is_deleted = 0").fetchone()[0],
        "resolved": db.execute("SELECT COUNT(*) FROM feedback WHERE status = 'resolved' AND is_deleted = 0").fetchone()[0],
    }

    return templates.TemplateResponse("admin/inbox.html", {
        "request": request,
        "user": user,
        "feedbacks": feedbacks,
        "stats": stats,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "total": total,
        "filter_status": status,
        "filter_category": category,
        "filter_tag": tag,
        "search": search or "",
        "allowed_tags": ALLOWED_TAGS,
    })


@app.get("/admin/feedback/{feedback_id}", response_class=HTMLResponse)
async def feedback_detail(
    request: Request,
    feedback_id: int,
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    row = db.execute("SELECT * FROM feedback WHERE id = ? AND is_deleted = 0", (feedback_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Feedback not found")

    feedback = dict(row)

    if feedback["status"] == "new":
        db.execute("UPDATE feedback SET status = 'read', updated_at = ? WHERE id = ?",
                    (datetime.utcnow().isoformat(), feedback_id))
        db.commit()
        feedback["status"] = "read"

    return templates.TemplateResponse("admin/detail.html", {
        "request": request,
        "user": user,
        "feedback": feedback,
    })


# ==================== API ENDPOINTS ====================

@app.post("/api/feedback/{feedback_id}/status")
async def update_status(
    feedback_id: int,
    request: Request,
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    data = await request.json()
    new_status = data.get("status")
    if new_status not in ("new", "read", "in_progress", "resolved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")

    db.execute("UPDATE feedback SET status = ?, updated_at = ? WHERE id = ?",
               (new_status, datetime.utcnow().isoformat(), feedback_id))
    db.commit()
    return {"ok": True}


@app.post("/api/feedback/{feedback_id}/note")
async def update_note(
    feedback_id: int,
    request: Request,
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    data = await request.json()
    note = data.get("note", "")
    db.execute("UPDATE feedback SET private_note = ?, updated_at = ? WHERE id = ?",
               (note, datetime.utcnow().isoformat(), feedback_id))
    db.commit()
    return {"ok": True}


@app.post("/api/feedback/bulk-status")
async def bulk_status(
    request: Request,
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    data = await request.json()
    ids = data.get("ids", [])
    new_status = data.get("status")
    if new_status not in ("new", "read", "in_progress", "resolved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    # Validate that all IDs are integers to prevent SQL injection
    try:
        ids = [int(id_val) for id_val in ids]
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Use parameterized query - build placeholders safely
    placeholders = ",".join("?" * len(ids))
    query = f"UPDATE feedback SET status = ?, updated_at = ? WHERE id IN ({placeholders})"
    
    db.execute(query, [new_status, datetime.utcnow().isoformat()] + ids)
    db.commit()
    return {"ok": True, "count": len(ids)}


@app.post("/api/feedback/{feedback_id}/delete")
async def soft_delete(
    feedback_id: int,
    user=Depends(require_role("admin")),
    db: sqlite3.Connection = Depends(get_db)
):
    db.execute("UPDATE feedback SET is_deleted = 1, updated_at = ? WHERE id = ?",
               (datetime.utcnow().isoformat(), feedback_id))
    db.commit()
    return {"ok": True}


# ==================== CSV EXPORT ====================

@app.get("/admin/export")
async def export_csv(
    request: Request,
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    rows = db.execute("""
        SELECT submission_id, category, message, status, detected_language,
               translation_en, translation_ru, summary, tags, private_note,
               ai_status, created_at, updated_at
        FROM feedback WHERE is_deleted = 0 ORDER BY created_at DESC
    """).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Submission ID", "Category", "Message", "Status", "Language",
        "Translation EN", "Translation RU", "Summary", "Tags",
        "Private Note", "AI Status", "Created At", "Updated At"
    ])
    for r in rows:
        writer.writerow([r[c] for c in range(len(r))])

    output.seek(0)
    filename = f"feedback_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== USER MANAGEMENT (Admin only) ====================

@app.get("/admin/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    user=Depends(require_role("admin")),
    db: sqlite3.Connection = Depends(get_db)
):
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": user,
        "users": [dict(u) for u in users],
    })


@app.post("/api/users")
async def create_user(
    request: Request,
    user=Depends(require_role("admin")),
    db: sqlite3.Connection = Depends(get_db)
):
    data = await request.json()
    email = data.get("email", "").strip()
    name = data.get("name", "").strip()
    password = data.get("password", "")
    role = data.get("role", "")

    if not email or not name or not password or role not in ("admin", "founder", "ceo"):
        raise HTTPException(status_code=400, detail="Invalid input")
    if len(password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")

    existing = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    db.execute(
        "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
        (email, hash_password(password), name, role)
    )
    db.commit()
    return {"ok": True}


@app.post("/api/users/{user_id}/toggle")
async def toggle_user(
    user_id: int,
    user=Depends(require_role("admin")),
    db: sqlite3.Connection = Depends(get_db)
):
    """Toggle user active status. Admin only."""
    target = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deactivating themselves
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    new_active = 0 if target["is_active"] else 1
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_active, user_id))
    db.commit()
    return {"ok": True, "is_active": new_active}


@app.post("/api/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    user=Depends(require_role("admin")),
    db: sqlite3.Connection = Depends(get_db)
):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return {"ok": True}


# ==================== ANALYTICS ====================

@app.get("/admin/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    by_category = db.execute("""
        SELECT category, COUNT(*) as cnt FROM feedback
        WHERE is_deleted = 0 GROUP BY category ORDER BY cnt DESC
    """).fetchall()

    by_status = db.execute("""
        SELECT status, COUNT(*) as cnt FROM feedback
        WHERE is_deleted = 0 GROUP BY status ORDER BY cnt DESC
    """).fetchall()

    by_tag = {}
    tag_rows = db.execute("SELECT tags FROM feedback WHERE is_deleted = 0 AND tags != '' AND tags IS NOT NULL").fetchall()
    for r in tag_rows:
        for t in r["tags"].split(","):
            t = t.strip()
            if t:
                by_tag[t] = by_tag.get(t, 0) + 1
    by_tag_sorted = sorted(by_tag.items(), key=lambda x: x[1], reverse=True)

    daily = db.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt FROM feedback
        WHERE is_deleted = 0 AND created_at >= DATE('now', '-30 days')
        GROUP BY DATE(created_at) ORDER BY day
    """).fetchall()

    return templates.TemplateResponse("admin/analytics.html", {
        "request": request,
        "user": user,
        "by_category": [dict(r) for r in by_category],
        "by_status": [dict(r) for r in by_status],
        "by_tag": by_tag_sorted,
        "daily": [dict(r) for r in daily],
    })
