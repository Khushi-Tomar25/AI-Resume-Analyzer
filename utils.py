"""
utils.py - Helper Functions & Utilities
----------------------------------------
Contains reusable utilities for text sanitization, regular expression parsing,
contact detail extraction, metric calculations, and formatting.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from config import ACTION_VERBS, QUANTIFIED_METRICS_PATTERN, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS

# ==========================================
# 1. Text Sanitization & Preprocessing
# ==========================================

def clean_text(text: str) -> str:
    """
    Cleans and standardizes raw text extracted from documents.
    Removes weird unicode artifacts, normalizes bullets, and reduces extra whitespace.
    """
    if not text:
        return ""
    
    # Replace common bullet symbols with a standard dash
    bullet_chars = [r"[\u2022\u2023\u25E6\u2043\u2219\u25CF\u25CB\u25AA\u25AB\u2013\u2014]"]
    for sym in bullet_chars:
        text = re.sub(sym, "-", text)
        
    # Replace non-breaking spaces and tabs with normal spaces
    text = text.replace("\xa0", " ").replace("\t", " ")
    
    # Normalize multiple newlines to at most two
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Normalize multiple spaces into single space
    lines = [re.sub(r"[ ]{2,}", " ", line).strip() for line in text.split("\n")]
    
    return "\n".join(lines).strip()


def extract_words(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9+#.-]+\b", text.lower())


def get_text_statistics(text: str) -> Dict[str, Any]:
    """
    Computes key text metrics such as word count, character count,
    line count, and estimated reading time.
    """
    cleaned = clean_text(text)
    words = extract_words(cleaned)
    word_count = len(words)
    char_count = len(cleaned)
    line_count = len([line for line in cleaned.split("\n") if line.strip()])
    
    # Average adult reading speed: ~200 words per minute
    reading_time_minutes = round(word_count / 200, 1) if word_count else 0
    
    # Approximate page count (standard 1 page is ~450-500 words)
    est_page_count = max(1, round(word_count / 450, 1)) if word_count else 0
    
    return {
        "word_count": word_count,
        "char_count": char_count,
        "line_count": line_count,
        "reading_time_minutes": reading_time_minutes,
        "est_page_count": est_page_count
    }


# ==========================================
# 2. Contact Information Extractors
# ==========================================

def extract_email(text: str) -> Optional[str]:
    """Extracts the first valid email address found in the text."""
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    match = re.search(email_pattern, text)
    return match.group(0).strip() if match else None


def extract_phone(text: str) -> Optional[str]:
    """
    Extracts phone numbers (supporting international, standard US,
    and Indian 10-digit mobile formats).
    """
    phone_pattern = r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}|\+?\d{1,3}[\s.-]?\d{10}|\b\d{10}\b)"
    matches = re.findall(phone_pattern, text)
    for m in matches:
        cleaned_match = re.sub(r"[\s().-]", "", m)
        # Verify it has between 10 and 15 digits (standard phone number lengths)
        if 10 <= len(cleaned_match) <= 15:
            return m.strip()
    return None


def extract_links(text: str) -> Dict[str, Optional[str]]:
    """
    Extracts LinkedIn, GitHub, and Portfolio / Personal website URLs from the text.
    """
    links: Dict[str, Optional[str]] = {
        "linkedin": None,
        "github": None,
        "portfolio": None
    }
    
    # LinkedIn pattern
    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?", text, re.IGNORECASE)
    if linkedin_match:
        links["linkedin"] = linkedin_match.group(0).strip()
        
    # GitHub pattern
    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?", text, re.IGNORECASE)
    if github_match:
        links["github"] = github_match.group(0).strip()
        
    # General Portfolio / Website pattern
    portfolio_match = re.search(r"(?:https?://)(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+(?:/[\w\-./?%&=]*)?", text)
    if portfolio_match:
        url = portfolio_match.group(0).strip()
        if not ("linkedin.com" in url or "github.com" in url):
            links["portfolio"] = url
            
    return links


def extract_candidate_name(text: str, email: Optional[str] = None) -> str:
    """
    Heuristically extracts candidate name from the top lines of the resume text.
    Uses capital letters, line length, and absence of common non-name headers.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return "Unknown Candidate"
    
    # Look at top 5 lines for name
    ignore_words = {"resume", "curriculum", "vitae", "cv", "page", "contact", "email", "phone", "address"}
    for line in lines[:5]:
        cleaned = re.sub(r"[^a-zA-Z\s]", "", line).strip()
        words = cleaned.split()
        # Candidate names are usually 2 to 4 words, each capitalized
        if 2 <= len(words) <= 4:
            if all(w.istitle() or w.isupper() for w in words):
                if not any(w.lower() in ignore_words for w in words):
                    return " ".join(words)
                    
    # Fallback to deriving from email if available
    if email:
        username = email.split("@")[0]
        name_parts = re.split(r"[._-]", username)
        if len(name_parts) >= 2:
            return " ".join([p.capitalize() for p in name_parts if p.isalpha()])
            
    return lines[0][:40].strip() if lines else "Candidate"


# ==========================================
# 3. Action Verbs & Quantified Metrics Detectors
# ==========================================

def extract_bullet_points(text: str) -> List[str]:
    """
    Extracts individual bullet points and accomplishment statements from text.
    """
    bullets = []
    lines = text.split("\n")
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        # Bullet indicator or short line with verb
        if line_s.startswith(("-", "*", "•", "–", "—")) or re.match(r"^\d+[\.\)]\s", line_s):
            cleaned_bullet = re.sub(r"^[-*•–—\d\.\)\s]+", "", line_s).strip()
            if len(cleaned_bullet) > 15:
                bullets.append(cleaned_bullet)
        elif len(line_s) > 25 and any(line_s.lower().startswith(v) for v in ACTION_VERBS):
            bullets.append(line_s)
            
    return bullets


def count_action_verbs(text: str) -> Tuple[int, List[str]]:
    """
    Counts distinct and total strong action verbs present in the resume.
    """
    words = extract_words(text)
    found_verbs = []
    for verb in ACTION_VERBS:
        if verb in words:
            found_verbs.append(verb)
    return len(found_verbs), sorted(found_verbs)


def extract_quantified_achievements(text: str) -> List[str]:
    """
    Finds quantified metrics, percentages, dollar values, and scale measurements.
    """
    matches = re.findall(QUANTIFIED_METRICS_PATTERN, text, re.IGNORECASE)
    # Deduplicate while preserving order
    seen = set()
    unique_matches = []
    for m in matches:
        m_clean = m.strip()
        if m_clean.lower() not in seen:
            seen.add(m_clean.lower())
            unique_matches.append(m_clean)
    return unique_matches


# ==========================================
# 4. Score Formatting & Grading Badges
# ==========================================

def get_score_badge(score: float) -> Dict[str, str]:
    """
    Returns visual badge attributes (label, hex color, description)
    based on a 0-100 score.
    """
    score = round(score, 1)
    if score >= 85:
        return {
            "label": "Excellent",
            "color": "#10B981",  # Emerald Green
            "badge_class": "badge-excellent",
            "message": "Highly optimized for ATS and recruiters. Strong impact!"
        }
    elif score >= 70:
        return {
            "label": "Good",
            "color": "#3B82F6",  # Blue
            "badge_class": "badge-good",
            "message": "Solid foundation. Minor keyword & metric optimizations will elevate it."
        }
    elif score >= 50:
        return {
            "label": "Average",
            "color": "#F59E0B",  # Amber/Yellow
            "badge_class": "badge-average",
            "message": "Moderate ATS compatibility. Missing key sections or quantified metrics."
        }
    else:
        return {
            "label": "Needs Improvement",
            "color": "#EF4444",  # Red
            "badge_class": "badge-poor",
            "message": "Low ATS pass probability. Action required on formatting, skills, and metrics."
        }


def validate_uploaded_file(file_name: str, file_size_bytes: int) -> Tuple[bool, str]:
    """
    Validates uploaded file against extension and file size limits.
    """
    ext = "." + file_name.split(".")[-1].lower() if "." in file_name else ""
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Please upload a PDF, DOCX, or TXT file."
    
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        return False, f"File size exceeds the {MAX_FILE_SIZE_MB}MB limit."
        
    return True, "File is valid."


def safe_json_dumps(obj: Any) -> str:
    """Safely serializes python objects to a JSON string."""
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return "{}"


def safe_json_loads(json_str: str) -> Any:
    """Safely parses JSON strings back to python objects."""
    if not json_str:
        return {}
    try:
        return json.loads(json_str)
    except Exception:
        return {}
