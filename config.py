"""
config.py - Central Configuration Module
-----------------------------------------
Contains all application constants, paths, skill taxonomies,
ATS scoring parameters, and Claude API settings.
"""

import os
from pathlib import Path

# Try loading .env variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==========================================
# 1. Project Paths
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
REPORTS_DIR = BASE_DIR / "reports"
SAMPLE_RESUMES_DIR = BASE_DIR / "sample_resumes"
DATA_DIR = BASE_DIR / "data"

# Ensure runtime directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_RESUMES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_PATH = DATA_DIR / "resume_analyzer.db"

# ==========================================
# 2. Secret & Configuration Resolution (Cloud + Local)
# ==========================================

def get_secret(key: str, default: str = "") -> str:
    """
    Retrieves configuration values with graceful multi-tier fallbacks:
    1. Streamlit Secrets (for Streamlit Community Cloud: st.secrets[key])
    2. Streamlit Secrets nested sections ([anthropic] or [general])
    3. Environment Variables (from .env or os.environ for local dev)
    4. Default fallback value
    """
    # 1. Streamlit Secrets (Community Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            # Direct key match (e.g. st.secrets["ANTHROPIC_API_KEY"])
            if key in st.secrets:
                val = st.secrets[key]
                if val is not None and str(val).strip():
                    return str(val).strip()
            
            # Lowercase key match
            if key.lower() in st.secrets:
                val = st.secrets[key.lower()]
                if val is not None and str(val).strip():
                    return str(val).strip()

            # Nested sections (e.g. [anthropic] api_key = "..." or [general])
            for section_name in ("anthropic", "general", "app"):
                if section_name in st.secrets:
                    sec = st.secrets[section_name]
                    try:
                        if key in sec and str(sec[key]).strip():
                            return str(sec[key]).strip()
                        if key.lower() in sec and str(sec[key.lower()]).strip():
                            return str(sec[key.lower()]).strip()
                        # Strip prefix e.g. ANTHROPIC_API_KEY -> api_key
                        short_key = key.lower().replace("anthropic_", "").replace("claude_", "")
                        if short_key in sec and str(sec[short_key]).strip():
                            return str(sec[short_key]).strip()
                    except Exception:
                        pass
    except Exception:
        pass

    # 2. Environment Variables (.env / os.environ)
    env_val = os.getenv(key, os.getenv(key.lower(), "")).strip()
    if env_val:
        return env_val

    return default


# ==========================================
# 3. Application & File Constraints
# ==========================================
APP_TITLE = "AI-Powered Resume Analyzer & ATS Optimizer"
APP_SUBTITLE = "Smart ATS scoring, deep skill gap analysis, and AI-driven career recommendations"
MAX_FILE_SIZE_MB = int(get_secret("MAX_FILE_SIZE_MB", "10"))
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt"]

# ==========================================
# 4. Anthropic Claude API Settings
# ==========================================
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY", "")
DEFAULT_CLAUDE_MODEL = get_secret(
    "ANTHROPIC_MODEL",
    get_secret("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
)
AVAILABLE_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307",
    "claude-3-opus-20240229"
]

# ==========================================
# 4. ATS Scoring Weights & Benchmark Rules
# ==========================================
# Total maximum score: 100
ATS_WEIGHTS = {
    "section_completeness": 20,  # Detection of essential sections
    "contact_info": 15,          # Email, Phone, LinkedIn/GitHub
    "action_verbs": 15,          # Strong action verbs in bullet points
    "quantified_impact": 15,     # Metrics, numbers, %, $
    "skills_density": 20,        # Count and relevance of identified skills
    "content_readability": 15    # Word count, formatting, bullet points
}

# Optimal Word Count ranges for single/two-page resume
OPTIMAL_WORD_COUNT_MIN = 350
OPTIMAL_WORD_COUNT_MAX = 1000

# Standard Resume Section Headers
STANDARD_SECTIONS = {
    "contact": ["contact", "personal info", "contact details"],
    "summary": ["summary", "professional summary", "career objective", "objective", "about me", "profile"],
    "experience": ["experience", "work experience", "employment history", "professional experience", "internships", "work history"],
    "education": ["education", "academic background", "qualifications", "academics", "educational qualification"],
    "skills": ["skills", "technical skills", "core competencies", "skills & expertise", "tech stack", "tools"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "notable projects"],
    "certifications": ["certifications", "licenses", "certificates", "courses", "professional credentials"],
    "achievements": ["achievements", "honors", "awards", "accomplishments", "extracurricular"]
}

# Strong Action Verbs for ATS evaluation
ACTION_VERBS = [
    "accelerated", "accomplished", "achieved", "acquired", "adapted", "administered",
    "advised", "allocated", "analyzed", "architected", "automated", "boosted",
    "budgeted", "built", "centralized", "championed", "collaborated", "compiled",
    "completed", "conceived", "conducted", "consolidated", "constructed", "coordinated",
    "crafted", "created", "customized", "debugged", "decreased", "delivered",
    "deployed", "designed", "developed", "devised", "diagnosed", "directed",
    "discovered", "doubled", "drafted", "drove", "eliminated", "enabled",
    "engineered", "enhanced", "established", "evaluated", "exceeded", "executed",
    "expanded", "expedited", "fabricated", "facilitated", "formulated", "fostered",
    "founded", "generated", "guided", "headed", "identified", "implemented",
    "improved", "increased", "initiated", "innovated", "inspected", "installed",
    "instituted", "instructed", "integrated", "introduced", "invented", "investigated",
    "launched", "led", "managed", "maximized", "mentored", "migrated", "minimized",
    "modernized", "monitored", "negotiated", "optimized", "orchestrated", "organized",
    "originated", "overhauled", "oversaw", "partnered", "performed", "pioneered",
    "planned", "prepared", "produced", "programmed", "promoted", "proposed",
    "re-engineered", "realized", "recommended", "reconciled", "recruited", "redesigned",
    "reduced", "refined", "reformed", "remodeled", "reorganized", "replaced",
    "researched", "resolved", "restructured", "revamped", "revitalized", "saved",
    "scaled", "scheduled", "screened", "secured", "simplified", "solved",
    "spearheaded", "standardized", "streamlined", "strengthened", "supervised", "surpassed",
    "tested", "trained", "transformed", "unified", "upgraded", "utilized", "validated"
]

# Quantified Impact Regex Pattern
QUANTIFIED_METRICS_PATTERN = r"(?:\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?|\b\d+\+?(?:\s*(?:k|m|million|billion|users|clients|customers|projects|hours|team members|engineers|requests|stars|downloads|sales|revenue))\b|\b(?:increased|decreased|reduced|saved|improved|boosted|grew)\s+by\s+\d+%)"

# ==========================================
# 5. Comprehensive Skill Taxonomies
# ==========================================
SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "dart", "html", "html5", "css", "css3", "sass",
        "bash", "shell", "powershell", "perl", "sql"
    ],
    "Web Frameworks & Libraries": [
        "react", "react.js", "angular", "vue", "vue.js", "next.js", "nuxt.js",
        "node.js", "express", "express.js", "django", "flask", "fastapi",
        "spring", "spring boot", "ruby on rails", "asp.net", "laravel",
        "tailwind css", "bootstrap", "material-ui", "redux", "graphql", "rest api"
    ],
    "Databases & Storage": [
        "postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra",
        "dynamodb", "elasticsearch", "neo4j", "mariadb", "firebase",
        "supabase", "oracle", "microsoft sql server", "snowflake", "bigquery"
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "azure", "google cloud", "gcp",
        "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
        "git", "github", "gitlab", "ci/cd", "circleci", "prometheus",
        "grafana", "linux", "nginx", "apache", "helm", "serverless", "lambda"
    ],
    "AI, ML & Data Science": [
        "machine learning", "deep learning", "artificial intelligence", "nlp",
        "natural language processing", "computer vision", "tensorflow", "pytorch",
        "scikit-learn", "keras", "opencv", "pandas", "numpy", "matplotlib",
        "seaborn", "llm", "large language models", "transformers", "hugging face",
        "langchain", "llamaindex", "rag", "embeddings", "bert", "gpt",
        "prompt engineering", "data analysis", "data visualization", "tableau", "power bi"
    ],
    "Software Engineering Practices": [
        "agile", "scrum", "kanban", "test driven development", "tdd",
        "microservices", "system design", "object oriented programming", "oop",
        "design patterns", "unit testing", "integration testing", "code review",
        "version control", "restful apis", "mvc", "data structures", "algorithms"
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "adaptability", "time management", "collaboration",
        "conflict resolution", "creativity", "work ethic", "attention to detail",
        "emotional intelligence", "decision making", "presentation skills",
        "negotiation", "mentorship", "project management"
    ],
    "Certifications": [
        "aws certified solutions architect", "aws certified developer", "aws certified cloud practitioner",
        "azure fundamentals", "azure solutions architect", "gcp certified professional",
        "pmp", "scrum master", "csm", "comptia security+", "comptia network+",
        "certified kubernetes administrator", "cka", "cissp", "ceh"
    ]
}

# Skill Alias / Normalization Map
SKILL_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "tf": "tensorflow",
    "sklearn": "scikit-learn",
    "mongo": "mongodb",
    "reactjs": "react",
    "vuejs": "vue",
    "nodejs": "node.js",
    "expressjs": "express",
    "nextjs": "next.js",
    "aws cloud": "aws",
    "google cloud platform": "google cloud",
    "amazon web services": "aws",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence"
}
