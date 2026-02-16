import json
import sqlite3
import threading
import logging
from datetime import datetime
from app.config import OPENAI_API_KEY, DATABASE_PATH, ALLOWED_TAGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_feedback_async(feedback_id: int):
    """
    Process feedback asynchronously in a background thread.
    Updates AI status and enriches feedback with translations, summary, and tags.
    """
    thread = threading.Thread(target=_process, args=(feedback_id,))
    thread.daemon = True
    thread.start()
    logger.info(f"Started AI processing for feedback {feedback_id}")


def _process(feedback_id: int):
    """Main processing function with comprehensive error handling."""
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    
    try:
        # Mark as processing
        db.execute("UPDATE feedback SET ai_status = 'processing' WHERE id = ?", (feedback_id,))
        db.commit()
        logger.info(f"Feedback {feedback_id}: Status set to 'processing'")

        # Fetch feedback
        row = db.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,)).fetchone()
        if not row:
            logger.warning(f"Feedback {feedback_id}: Not found in database")
            return

        message = row["message"] or ""
        if not message.strip():
            logger.info(f"Feedback {feedback_id}: Empty message, marking as done")
            db.execute(
                "UPDATE feedback SET ai_status = 'done', summary = '', translation_en = '', translation_ru = '', tags = '', detected_language = 'unknown' WHERE id = ?",
                (feedback_id,))
            db.commit()
            return

        # Process with OpenAI or fallback
        if OPENAI_API_KEY:
            logger.info(f"Feedback {feedback_id}: Processing with OpenAI")
            _process_with_openai(db, feedback_id, message)
        else:
            logger.info(f"Feedback {feedback_id}: Processing with fallback (no API key)")
            _process_fallback(db, feedback_id, message)

    except Exception as e:
        logger.error(f"Feedback {feedback_id}: Unexpected error - {type(e).__name__}: {str(e)}", exc_info=True)
        try:
            db.execute("UPDATE feedback SET ai_status = 'failed' WHERE id = ?", (feedback_id,))
            db.commit()
        except Exception as db_error:
            logger.error(f"Feedback {feedback_id}: Failed to update status to 'failed' - {str(db_error)}")
    finally:
        db.close()


def _process_with_openai(db, feedback_id, message):
    """
    Process feedback using OpenAI API with comprehensive error handling.
    Handles: timeout, rate limits, invalid key, quota exceeded, network errors.
    """
    try:
        from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError, APITimeoutError
        
        # Create client with timeout
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=30.0,  # 30 second timeout
            max_retries=2   # Retry twice on transient errors
        )

        tags_list = ", ".join(ALLOWED_TAGS)
        prompt = f"""Analyze this anonymous employee feedback message. Return ONLY valid JSON with these fields:
- "detected_language": ISO 639-1 code of the original message language
- "translation_en": English translation (if already English, copy as-is)
- "translation_ru": Russian translation
- "summary": 1-2 sentence summary in English (max 150 chars)
- "tags": array of 1-3 tags from this list ONLY: [{tags_list}]

Rules:
- Only transform/structure the text, do NOT add new facts
- Preserve cannabis terminology and slang meaning
- Summary must reflect the key issue or idea

Message: \"\"\"{message}\"\"\""""

        logger.info(f"Feedback {feedback_id}: Sending request to OpenAI")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1000
        )

        result = json.loads(response.choices[0].message.content)
        logger.info(f"Feedback {feedback_id}: Received response from OpenAI")

        # Validate and filter tags
        tags = result.get("tags", [])
        if isinstance(tags, list):
            tags = [t for t in tags if t in ALLOWED_TAGS]
            tags_str = ",".join(tags)
        else:
            tags_str = ""

        # Update database
        db.execute("""
            UPDATE feedback SET
                ai_status = 'done',
                detected_language = ?,
                translation_en = ?,
                translation_ru = ?,
                summary = ?,
                tags = ?
            WHERE id = ?
        """, (
            result.get("detected_language", "unknown"),
            result.get("translation_en", ""),
            result.get("translation_ru", ""),
            result.get("summary", "")[:150],
            tags_str,
            feedback_id
        ))
        db.commit()
        logger.info(f"Feedback {feedback_id}: Successfully processed with OpenAI")

    except AuthenticationError as e:
        # Invalid API key
        logger.error(f"Feedback {feedback_id}: OpenAI authentication failed - Invalid API key: {str(e)}")
        _fallback_on_error(db, feedback_id, message, "Authentication failed (invalid API key)")
        
    except RateLimitError as e:
        # Rate limit exceeded
        logger.warning(f"Feedback {feedback_id}: OpenAI rate limit exceeded: {str(e)}")
        _fallback_on_error(db, feedback_id, message, "Rate limit exceeded")
        
    except APITimeoutError as e:
        # Request timeout
        logger.warning(f"Feedback {feedback_id}: OpenAI request timeout: {str(e)}")
        _fallback_on_error(db, feedback_id, message, "Request timeout")
        
    except APIConnectionError as e:
        # Network/connection error
        logger.warning(f"Feedback {feedback_id}: OpenAI connection error: {str(e)}")
        _fallback_on_error(db, feedback_id, message, "Connection error")
        
    except APIError as e:
        # Other API errors (quota exceeded, server error, etc.)
        logger.error(f"Feedback {feedback_id}: OpenAI API error: {str(e)}")
        _fallback_on_error(db, feedback_id, message, f"API error: {e.message if hasattr(e, 'message') else str(e)}")
        
    except json.JSONDecodeError as e:
        # Invalid JSON response
        logger.error(f"Feedback {feedback_id}: Failed to parse OpenAI response: {str(e)}")
        _fallback_on_error(db, feedback_id, message, "Invalid response format")
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Feedback {feedback_id}: Unexpected error in OpenAI processing: {type(e).__name__}: {str(e)}", exc_info=True)
        _fallback_on_error(db, feedback_id, message, f"Unexpected error: {type(e).__name__}")


def _fallback_on_error(db, feedback_id, message, error_reason):
    """
    Fallback to keyword-based processing when OpenAI fails.
    Logs the error reason and processes with fallback method.
    """
    logger.info(f"Feedback {feedback_id}: Falling back to keyword-based processing due to: {error_reason}")
    try:
        _process_fallback(db, feedback_id, message)
    except Exception as e:
        logger.error(f"Feedback {feedback_id}: Fallback processing also failed: {str(e)}", exc_info=True)
        db.execute("UPDATE feedback SET ai_status = 'failed' WHERE id = ?", (feedback_id,))
        db.commit()


def _process_fallback(db, feedback_id, message):
    """Fallback when no OpenAI key - basic processing with heuristics."""
    import re

    logger.info(f"Feedback {feedback_id}: Starting fallback processing")

    # Generate summary (first 150 chars)
    summary = message[:147] + "..." if len(message) > 150 else message

    # Keyword-based tagging
    tags = []
    keywords_map = {
        "Salary": ["salary", "pay", "wage", "money", "bonus", "compensation", "เงินเดือน"],
        "Store": ["store", "shop", "location", "branch", "ร้าน"],
        "Product": ["product", "strain", "weed", "cannabis", "flower", "edible", "สินค้า"],
        "Conflict": ["conflict", "fight", "argue", "bully", "harass", "toxic", "ทะเลาะ"],
        "Legal": ["legal", "law", "license", "regulation", "กฎหมาย"],
        "Management": ["manager", "boss", "supervisor", "lead", "ผู้จัดการ"],
        "Schedule": ["schedule", "shift", "overtime", "hours", "time", "ตารางงาน"],
        "Safety": ["safety", "danger", "risk", "accident", "unsafe", "ความปลอดภัย"],
        "Training": ["training", "learn", "skill", "course", "การฝึกอบรม"],
        "Equipment": ["equipment", "tool", "broken", "fix", "repair", "อุปกรณ์"],
        "Customer": ["customer", "client", "complaint", "ลูกค้า"],
        "Policy": ["policy", "rule", "procedure", "นโยบาย"],
        "Communication": ["communication", "inform", "meeting", "การสื่อสาร"],
        "Hygiene": ["clean", "dirty", "hygiene", "sanit", "สะอาด"],
    }

    msg_lower = message.lower()
    for tag, kws in keywords_map.items():
        for kw in kws:
            if kw in msg_lower:
                tags.append(tag)
                break
        if len(tags) >= 3:
            break

    if not tags:
        tags = ["Other"]

    logger.info(f"Feedback {feedback_id}: Detected tags: {tags}")

    # Detect language (simple heuristic)
    has_thai = bool(re.search(r'[\u0E00-\u0E7F]', message))
    has_cyrillic = bool(re.search(r'[\u0400-\u04FF]', message))
    has_chinese = bool(re.search(r'[\u4E00-\u9FFF]', message))
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', message))
    
    if has_thai:
        detected = "th"
    elif has_cyrillic:
        detected = "ru"
    elif has_chinese:
        detected = "zh"
    elif has_arabic:
        detected = "ar"
    else:
        detected = "en"

    logger.info(f"Feedback {feedback_id}: Detected language: {detected}")

    # Update database
    db.execute("""
        UPDATE feedback SET
            ai_status = 'done',
            detected_language = ?,
            translation_en = ?,
            translation_ru = ?,
            summary = ?,
            tags = ?
        WHERE id = ?
    """, (
        detected,
        message if detected == "en" else f"[Auto-translation unavailable] {message}",
        f"[Требуется перевод] {message}",
        summary,
        ",".join(tags),
        feedback_id
    ))
    db.commit()
    logger.info(f"Feedback {feedback_id}: Fallback processing completed successfully")
