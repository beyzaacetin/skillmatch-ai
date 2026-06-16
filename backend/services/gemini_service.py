import google.generativeai as genai
import os
import json
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
import models
from config import settings

logger = logging.getLogger(__name__)

# Configure Google GenAI
API_KEY = settings.GEMINI_API_KEY
if API_KEY:
    genai.configure(api_key=API_KEY)


def call_gemini(db: Session, prompt: str, system_instruction: str = None, json_mode: bool = False) -> str:
    """
    Centralized wrapper for Gemini API calls.
    Logs every prompt and response into the ai_requests table.
    Handles rate limit, timeout, and key errors explicitly.
    """
    model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
    
    # 1. API Key Check
    if not settings.GEMINI_API_KEY:
        error_msg = "Gemini API key missing"
        # Log error to DB
        _log_to_db(db, prompt, None, model_name, error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        # Prepare model
        generation_config = {}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        # Initialize model
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config=generation_config
        )

        # 2. Generate content
        response = model.generate_content(prompt)
        response_text = response.text

        # Validate JSON if json_mode
        if json_mode:
            try:
                # Basic JSON check
                json.loads(response_text)
            except Exception:
                # Attempt to extract JSON from markdown block
                cleaned = response_text.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    cleaned = "\n".join(lines).strip()
                
                # Check again
                try:
                    json.loads(cleaned)
                    response_text = cleaned
                except Exception:
                    error_msg = "Invalid response (Failed to parse JSON)"
                    _log_to_db(db, prompt, response_text, model_name, error_msg)
                    raise HTTPException(status_code=500, detail="Invalid response")

        # Log success
        _log_to_db(db, prompt, response_text, model_name, None)
        return response_text

    except HTTPException as he:
        # Re-raise FastAPIs exceptions
        raise he

    except Exception as e:
        err_str = str(e).lower()
        error_msg = "Backend error"
        status_code = 500

        if "api_key" in err_str or "api key" in err_str or "unauthorized" in err_str:
            error_msg = "Gemini API key missing"
            status_code = 400
        elif "timeout" in err_str or "deadline" in err_str:
            error_msg = "Gemini timeout"
            status_code = 504
        elif "429" in err_str or "rate limit" in err_str or "quota" in err_str or "resource exhausted" in err_str:
            error_msg = "Gemini rate limit"
            status_code = 429
        else:
            error_msg = f"Backend error: {str(e)}"

        # Log error to DB
        _log_to_db(db, prompt, None, model_name, error_msg)
        raise HTTPException(status_code=status_code, detail=error_msg)


def _log_to_db(db: Session, prompt: str, response: str, model_name: str, error: str):
    """Logs the request metadata safely to SQLite/PostgreSQL."""
    try:
        req_log = models.AIRequest(
            prompt=prompt,
            response=response,
            model_name=model_name,
            error=error
        )
        db.add(req_log)
        db.commit()
    except Exception as db_err:
        logger.error(f"Failed to log AI request to database: {db_err}")
        db.rollback()
