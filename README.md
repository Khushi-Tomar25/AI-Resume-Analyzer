# 🚀 ResumeAI: AI-Powered Resume Analyzer & ATS Optimizer

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit App](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io)
[![Claude AI](https://img.shields.io/badge/Anthropic-Claude%203.5%20Sonnet-6B21A8.svg)](https://anthropic.com)
[![Pytest](https://img.shields.io/badge/Pytest-Passing%2028%2F28-success.svg)](https://pytest.org)
[![OS: Windows Ready](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-0078D6.svg)](https://microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, student-friendly web application designed to help job seekers, students, and professionals analyze resumes, measure ATS (Applicant Tracking System) compatibility, compare resumes with target job descriptions, uncover skill gaps, and receive honest, metric-driven recommendations powered by **Anthropic Claude 3.5 Sonnet** and **ReportLab**.

---

## 📌 Table of Contents
1. [Project Introduction](#-project-introduction)
2. [Problem Statement](#-problem-statement)
3. [Project Objectives](#-project-objectives)
4. [Key Features](#-key-features)
5. [Technologies Used](#-technologies-used)
6. [System Architecture & Folder Structure](#-system-architecture--folder-structure)
7. [Role of Each Python Module](#-role-of-each-python-module)
8. [Windows Local Setup Guide](#-windows-local-setup-guide)
9. [API Key Configuration](#-api-key-configuration)
10. [Running the Application](#-running-the-application)
11. [Testing Instructions](#-testing-instructions)
12. [Future Deployment Readiness Guide](#-future-deployment-readiness-guide)
13. [Migrating from SQLite to a Hosted Database](#-migrating-from-sqlite-to-a-hosted-database)
14. [Security & Privacy Practices](#-security--privacy-practices)
15. [Limitations & Future Scope](#-limitations--future-scope)
16. [Academic & College Submission Note](#-academic--college-submission-note)

---

## 📖 Project Introduction

**ResumeAI** is an intelligent resume auditing and optimization platform. Combining Natural Language Processing (NLP), TF-IDF semantic vector similarity, regular expression parsing engines, embedded SQLite persistence, and Anthropic's Claude 3.5 Sonnet Large Language Model, ResumeAI demystifies the automated screening algorithms used by modern recruitment platforms.

---

## 🛑 Problem Statement

Modern recruitment processes rely heavily on automated **Applicant Tracking Systems (ATS)** such as Workday, Taleo, Greenhouse, and Lever to filter high volumes of applications. Industry estimates indicate that **up to 75% of resumes are rejected automatically** before a human recruiter ever sees them.

Common causes of rejection include:
- Unparsable multi-column layouts, tables, or scanned image documents lacking extractable text.
- Missing industry-standard keywords and taxonomy alignment with the target job posting.
- Passive descriptions of daily duties rather than quantifiable accomplishments.
- Lack of essential sections, broken links, or non-standard formatting.

Job applicants often submit hundreds of resumes without receiving feedback on why they were rejected. ResumeAI solves this problem by giving applicants transparent, instant, and actionable feedback.

---

## 🎯 Project Objectives

1. **Automated Multi-Format Parsing**: Extract raw text, contact info, and structural sections from PDF, DOCX, and TXT resumes without data loss.
2. **Transparent ATS Scoring**: Provide an explainable 6-pillar score (0–100) assessing contact validity, section completeness, action verbs, quantified results, skill density, and readability.
3. **Job Description Matching**: Measure exact skill matches, discover partially matching/adjacent technologies, and calculate semantic TF-IDF text similarity against real job descriptions.
4. **Honest AI Improvements**: Use Claude 3.5 Sonnet to provide "Original vs. Suggested" bullet rewrites using Google's XYZ formula (*Accomplished [X] measured by [Y] by doing [Z]*), while prompting the user for real numbers rather than fabricating achievements.
5. **Report Generation**: Export downloadable, professionally formatted PDF audit summaries using ReportLab.
6. **Privacy-First Architecture**: Keep parsing, scoring, and history completely local, only connecting to external AI when explicitly requested.

---

## ✨ Key Features

- **Multi-Format Extraction Pipeline**: Robust parsing supporting `.pdf` (PyMuPDF with multiple fallbacks), `.docx` (python-docx with XML extraction), and `.txt`.
- **Scanned PDF Detection**: Accurately detects image-only or raster PDFs that lack extractable text streams and alerts the candidate that OCR or digital export is required.
- **6-Pillar Transparent ATS Scorer**:
  - *Contact Information & Online Presence* (10%)
  - *Section Completeness & History* (20%)
  - *Action Verbs & Leadership* (15%)
  - *Quantified Achievements & Metrics* (20%)
  - *Skills Keyword Density* (20%)
  - *Document Structure & Readability* (15%)
- **Hybrid Job Compatibility Engine**:
  - Computes a 4-factor hybrid score: 40% Exact Skills + 15% Partial Credit + 30% TF-IDF Cosine + 15% Top Keywords.
  - Identifies adjacent competencies (e.g. MySQL when JD asks for PostgreSQL; Vue when JD asks for React; AWS when JD asks for GCP).
  - Benchmarks target years of experience against resume evidence.
- **Dedicated Resume Improvement Engine**:
  - Side-by-side **Original Content vs. Suggested Content**.
  - Upgrades bullet points using Google's XYZ formula.
  - Generates 3 tailored professional summaries.
  - Provides a 30-day learning roadmap for missing skills.
  - Prompts user to input true metrics instead of hallucinating credentials.
- **Executive Results Dashboard**:
  - Overall Resume Scorecard.
  - Interactive Bar Chart showing skills distribution across categories.
  - Color-coded matching vs. missing skill badges.
- **Local SQLite History & Multi-Tenant Readiness**:
  - Stores scan summaries and metadata in `data/resume_analyzer.db`.
  - Open/Reload historical scans into the dashboard or delete individual records.
  - Includes `user_id` schema support for future multi-user authentication.
- **Downloadable PDF Reports**:
  - Two-pass `NumberedCanvas` generating *"Page X of Y"* on every page.
  - Scorecard, tables, missing skills, and AI action items.

---

## 🛠️ Technologies Used

| Layer | Technologies | Role / Purpose |
|---|---|---|
| **Frontend UI** | Streamlit 1.35+, HTML5, Custom CSS | Modern SaaS dashboard, responsive layout, tabs |
| **Backend Language** | Python 3.10+ | Core business logic, parsing, and algorithms |
| **AI Integration** | Anthropic Python SDK (`anthropic`) | Claude 3.5 Sonnet for deep critiques & XYZ rewrites |
| **Document Processing** | PyMuPDF (`pymupdf`), python-docx | Text extraction from PDF & DOCX documents |
| **NLP & Similarity** | scikit-learn (`TfidfVectorizer`, cosine similarity) | Semantic text overlap and keyword frequency |
| **Database** | SQLite (`sqlite3`) | Embedded persistent storage for scan history |
| **PDF Generation** | ReportLab (`reportlab`) | Executive PDF evaluation reports with page numbers |
| **Testing** | pytest | 28 automated unit tests covering all modules |
| **Environment** | python-dotenv | Secure API credential management |

---

## 📁 System Architecture & Folder Structure

```
AI_Resume_Analyzer/
│
├── app.py                      # Main Streamlit web application & interactive UI
├── ai_analyzer.py              # Anthropic Claude 3.5 Sonnet client & prompt engineering
├── resume_parser.py            # PDF, DOCX, & TXT multi-engine extraction pipeline
├── ats_scorer.py               # 6-pillar ATS scoring algorithm (0-100)
├── job_matcher.py              # TF-IDF cosine similarity & hybrid skill gap matcher
├── skill_extractor.py          # Configurable taxonomy & boundary-safe skill engine
├── report_generator.py         # ReportLab professional PDF report generator
├── database.py                 # SQLite persistence layer for scan history & analytics
├── utils.py                    # Reusable text cleaning, regex, and formatting helpers
├── config.py                   # Central settings, ATS weights, & skill taxonomy
│
├── requirements.txt            # Pinned, cross-platform dependencies
├── .env                        # Local environment variables (API keys)
├── .env.example                # Configuration template
├── .gitignore                  # Git ignore rules for virtualenvs, caches, & reports
├── README.md                   # Complete documentation
│
├── assets/
│   ├── styles.css              # Custom modern Streamlit CSS styles
│   └── logo.png                # Application branding logo
│
├── data/
│   └── resume_analyzer.db      # Local SQLite database
│
├── reports/
│   └── .gitkeep                # Directory for generated PDF audit reports
│
├── sample_resumes/             # Pre-loaded sample resumes for instant testing
│   ├── software_engineer_resume.txt
│   ├── software_engineer_resume.pdf
│   ├── fresher_resume.txt
│   └── fresher_resume.docx
│
└── tests/                      # Automated test suite (28 tests)
    ├── test_ats_scorer.py
    ├── test_database.py
    ├── test_job_matcher.py
    ├── test_report_generator.py
    ├── test_resume_parser.py
    └── test_skill_extractor.py
```

---

## 🔍 Role of Each Python Module

- **[app.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/app.py)**: The central presentation layer. Orchestrates the 7-page navigation (*Home*, *Resume Analyzer*, *ATS Score*, *Job Description Matcher*, *Resume Improvement*, *Analysis History*, *About*), renders KPI scorecards, charts, and file uploaders.
- **[resume_parser.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/resume_parser.py)**: Handles file format validation (magic byte checks), file size limits (10MB), scanned document detection, and section segmentation (*Experience*, *Education*, *Skills*, *Projects*, *Summary*).
- **[ats_scorer.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/ats_scorer.py)**: Calculates the transparent 0–100 ATS compatibility score across 6 pillars with weights, feedback, and commercial ATS disclaimers. 100% independent of external APIs.
- **[job_matcher.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/job_matcher.py)**: Computes TF-IDF cosine similarity, identifies exact vs. partial matching skills, detects missing skills, and checks experience requirement alignment.
- **[skill_extractor.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/skill_extractor.py)**: Boundary-safe taxonomy engine categorizing skills into Programming Languages, Frameworks, Tools, Technical Skills, and Soft Skills. Supports runtime custom dictionary expansion.
- **[ai_analyzer.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/ai_analyzer.py)**: Secure client for Claude 3.5 Sonnet. Generates structured 14-dimension audits and Original vs. Suggested rewrites without hallucinating facts. Provides offline local fallback.
- **[report_generator.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/report_generator.py)**: ReportLab PDF engine using a two-pass `NumberedCanvas` to generate clean, downloadable reports with scorecards, tables, and page numbers.
- **[database.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/database.py)**: SQLite interface managing scan history, individual record deletion, reload actions, and future `user_id` multi-tenant support.
- **[utils.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/utils.py)**: Helper library for text sanitization, email/phone regex extraction, action verb counting, and metric formatting.
- **[config.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/config.py)**: Central repository of portable paths (`pathlib.Path`), skill taxonomy constants, and scoring weights.

---

## 🪟 Windows Local Setup Guide

The project is fully tested on **Windows 10 and Windows 11** using PowerShell or Command Prompt.

### Step 1: Open your terminal inside the project directory
```powershell
cd c:\Users\prash\OneDrive\Documents\Desktop\projects\Ai_Resume
```

### Step 2: Create a virtual environment
```powershell
python -m venv venv
```

### Step 3: Activate the virtual environment
- **In Command Prompt (cmd.exe):**
  ```cmd
  venv\Scripts\activate
  ```
- **In Windows PowerShell:**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(Note: If PowerShell displays an `Execution_Policies` restriction, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once, then activate).*

### Step 4: Install all required dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Run automated test suite
```powershell
pytest -v
```

### Step 6: Start the application
```powershell
streamlit run app.py
```
The application will launch automatically in your browser at `http://localhost:8501`.

---

## 🔑 API Key Configuration

The application includes an **intelligent offline fallback**, meaning you can test and run all document parsing, ATS scoring, skill extraction, job matching, and PDF generation **without an API key**.

To unlock live Claude 3.5 Sonnet AI critiques and dynamic bullet point rewrites:
1. Create a `.env` file based on `.env.example`:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` and set your key:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
   ```
*(You can also enter your key directly in the web app sidebar at runtime!)*

---

## ☁️ Future Deployment Readiness Guide

The codebase has been engineered specifically for zero-friction cloud deployment (Streamlit Community Cloud, Docker, Render, Railway, or AWS):

1. **Zero Hardcoded Personal File Paths**:
   All paths are dynamically constructed using Python's standard `pathlib.Path(__file__).resolve().parent`. The project runs identically on Windows (`C:\...`), Linux (`/home/...`), and Docker (`/app/...`).
2. **Environment Variable Configuration**:
   All sensitive keys, model choices, and file limits are read via `os.getenv()`.
3. **In-Memory File Processing**:
   Uploaded resumes are processed in-memory as byte streams during the Streamlit session. No temporary or unmanaged files are left behind.
4. **Automated Directory Initialization**:
   Required runtime folders (`data/`, `reports/`, `sample_resumes/`) are automatically verified and created by `config.py` upon startup.

### Deploying to Streamlit Community Cloud (Quickest Free Method)
1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Click **"New App"** and select your repository, branch (`main`), and entry point (`app.py`).
4. Under **"Advanced Settings" -> "Secrets"**, enter:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-api03-..."
   ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
   ```
5. Click **"Deploy"**. Streamlit Cloud will install packages from `requirements.txt` and launch the app with a public URL.

### Deploying with Docker
A production `Dockerfile` for containerized hosting:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 🗄️ Migrating from SQLite to a Hosted Database

The current application uses embedded **SQLite** via [database.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/database.py). Because SQLite stores data in a local file (`data/resume_analyzer.db`), serverless cloud containers may reset this file on restart.

When migrating to a persistent hosted database (e.g. **PostgreSQL**, **Neon**, or **Supabase**), only two simple changes in [database.py](file:///c:/Users/prash/OneDrive/Documents/Desktop/projects/Ai_Resume/database.py) are needed:

### 1. Install PostgreSQL adapter
Add `psycopg2-binary>=2.9.0` or `sqlalchemy>=2.0.0` to `requirements.txt`:
```bash
pip install psycopg2-binary
```

### 2. Update Connection Method in `database.py`
Replace the local SQLite connection with a cloud database URI:
```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. postgresql://user:pass@ep-cool-db.neon.tech/neondb

def get_connection(self):
    if DATABASE_URL:
        # Hosted PostgreSQL connection
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        # Fallback to local SQLite for offline development
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
```
The table schema, SQL queries (`INSERT`, `SELECT`, `DELETE`), and `user_id` multi-tenant fields are already ANSI SQL standard and fully compatible with PostgreSQL.

---

## 🔒 Security & Privacy Practices

- **Zero Involuntary Cloud Storage**: Resume files are processed in-memory during the Streamlit session and are **never uploaded to external cloud storage**.
- **Local SQLite Database**: Historical records are kept exclusively on the local machine hosting the app in `data/resume_analyzer.db`.
- **API Secret Masking**: Anthropic API credentials are never logged, never saved in git, and masked in the UI (`sk-ant...xxxx`).
- **Input Sanitization**: File magic bytes are validated (`%PDF-`, `PK\x03\x04`), file sizes are capped at 10MB, and content is never executed as code.
- **AI Transparency**: The application clearly marks when data is processed locally vs. when it is sent to Anthropic's Claude API.

---

## ⚠️ Limitations & Future Scope

### Limitations
1. **Scanned PDF Optical Character Recognition (OCR)**: Scanned image-only PDFs do not contain selectable text streams. The system detects scanned PDFs and alerts the candidate, but full OCR requires external OCR engines like Tesseract.
2. **Proprietary Vendor Algorithms**: Every company configures commercial ATS platforms (Workday, Taleo, Greenhouse) with custom filters and human recruiter preferences. ResumeAI provides an estimated benchmark based on open best practices rather than a single vendor's black-box algorithm.
3. **Live AI Network Dependency**: Live Claude 3.5 Sonnet calls require an active internet connection and API quota. When offline, high-quality rule-based templates run locally.

### Future Scope
- **Optical Character Recognition (OCR)**: Integrate Tesseract or PyMuPDF OCR to process image-only scanned paper resumes.
- **Multi-Tenant User Authentication**: Implement user login, JWT tokens, and role-based permissions utilizing the existing `user_id` database schema.
- **Interactive Resume Editor**: An in-browser WYSIWYG editor allowing candidates to edit suggestions directly and re-score in real time.
- **LinkedIn / GitHub Profile Scraper**: Auto-import candidate achievements directly from professional profiles.
- **Cover Letter Generator**: Generate tailored, role-specific cover letters mirroring the candidate's verified resume accomplishments.

---

## 🎓 Academic & College Submission Note

This project was built to demonstrate proficiency in:
- **Full-Stack Python Web Development**: Streamlit, HTML5, Custom CSS, Responsive Layouts.
- **Natural Language Processing & Information Retrieval**: TF-IDF, Cosine Similarity, Regular Expressions, Word-Boundary Tokenization.
- **Large Language Model (LLM) Integration & Prompt Engineering**: Anthropic Claude 3.5 Sonnet SDK, Google XYZ Formula, Anti-Hallucination Constraints.
- **Software Engineering Best Practices**: Decoupled Modular Services, 28 Automated Pytest Unit Tests, Environment Security.
- **Relational Database Management**: SQLite, Schema Migrations, Multi-Tenant Preparedness.
- **Enterprise Document Publishing**: ReportLab, Custom Canvas Two-Pass Page Numbering.

---

## 📄 License
This project is licensed under the MIT License.
