"""
test_resume_parser.py - Unit tests for resume_parser.py and utils.py
"""

import pytest
from pathlib import Path
from resume_parser import parse_resume, ResumeParser
from utils import extract_email, extract_phone, extract_links, clean_text, extract_candidate_name

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_resumes"


def test_clean_text():
    raw = "  John   Doe  \n\n\n• Point 1\xa0• Point 2  "
    cleaned = clean_text(raw)
    assert "- Point 1" in cleaned
    assert "  " not in cleaned


def test_contact_extraction():
    sample_text = """
    Jane Developer
    jane.dev@example.com | (555) 123-4567 | San Francisco, CA
    https://linkedin.com/in/janedev | https://github.com/janedev-code
    """
    email = extract_email(sample_text)
    phone = extract_phone(sample_text)
    links = extract_links(sample_text)

    assert email == "jane.dev@example.com"
    assert phone is not None and "123" in phone
    assert links["linkedin"] == "https://linkedin.com/in/janedev"
    assert links["github"] == "https://github.com/janedev-code"


def test_candidate_name_extraction():
    text = "Alex Mercer\nalex.mercer@test.com\nSoftware Engineer"
    name = extract_candidate_name(text, email="alex.mercer@test.com")
    assert name == "Alex Mercer"


def test_section_identification():
    parser = ResumeParser()
    text = """
    John Doe
    john@example.com

    PROFESSIONAL SUMMARY
    Experienced developer.

    WORK EXPERIENCE
    Software Engineer at TechCorp. Built web apps.

    EDUCATION
    BS in Computer Science.

    TECHNICAL SKILLS
    Python, React, SQL.
    """
    sections = parser.identify_sections(text)
    assert "experience" in sections
    assert "education" in sections
    assert "skills" in sections
    assert "Python" in sections["skills"]


def test_parse_sample_txt():
    txt_path = SAMPLE_DIR / "software_engineer_resume.txt"
    if txt_path.exists():
        result = parse_resume(str(txt_path), file_name="software_engineer_resume.txt")
        assert result["candidate_name"] == "Alex Morgan"
        assert result["email"] == "alex.morgan@example.com"
        assert "experience" in result["sections"]
        assert result["statistics"]["word_count"] > 100
        assert result["parsing_status"] == "success"


def test_parse_sample_pdf():
    pdf_path = SAMPLE_DIR / "software_engineer_resume.pdf"
    if pdf_path.exists():
        result = parse_resume(str(pdf_path), file_name="software_engineer_resume.pdf")
        assert result["file_type"] == "pdf"
        assert len(result["clean_text"]) > 100
        assert "alex.morgan@example.com" in result["clean_text"]
        assert result["parsing_status"] == "success"


def test_parse_sample_docx():
    docx_path = SAMPLE_DIR / "fresher_resume.docx"
    if docx_path.exists():
        result = parse_resume(str(docx_path), file_name="fresher_resume.docx")
        assert result["file_type"] == "docx"
        assert len(result["clean_text"]) > 50
        assert "Priya Sharma" in result["clean_text"]
        assert result["parsing_status"] == "success"


def test_empty_file_validation():
    parser = ResumeParser()
    res = parser.parse(b"", file_name="empty.pdf")
    assert res["parsing_status"] == "error"
    assert "empty" in res["error_message"].lower()


def test_corrupted_pdf_validation():
    parser = ResumeParser()
    # Invalid bytes that don't start with %PDF-
    res = parser.parse(b"This is not a real PDF file header", file_name="broken.pdf")
    assert res["parsing_status"] == "error"
    assert "corrupted" in res["error_message"].lower()


def test_corrupted_docx_validation():
    parser = ResumeParser()
    # Invalid bytes that don't start with PK\x03\x04
    res = parser.parse(b"This is not a real docx archive", file_name="broken.docx")
    assert res["parsing_status"] == "error"
    assert "corrupted" in res["error_message"].lower()


def test_parse_sample_txt_bytes():
    txt_path = SAMPLE_DIR / "software_engineer_resume.txt"
    if txt_path.exists():
        result = parse_resume(txt_path.read_bytes(), file_name=txt_path.name)
        assert result["candidate_name"] == "Alex Morgan"
        assert result["parsing_status"] == "success"
        assert len(result["clean_text"]) > 100


def test_parse_fresher_txt_bytes():
    txt_path = SAMPLE_DIR / "fresher_resume.txt"
    if txt_path.exists():
        result = parse_resume(txt_path.read_bytes(), file_name=txt_path.name)
        assert result["candidate_name"] == "Priya Sharma"
        assert result["parsing_status"] == "success"
        assert len(result["clean_text"]) > 100


def test_parse_raw_text_string_no_file_not_found():
    raw_content = "John Doe\njohn@example.com\n\nSUMMARY\nSoftware Engineer with experience."
    result = parse_resume(raw_content, file_name="sample.txt")
    assert result["candidate_name"] == "John Doe"
    assert result["parsing_status"] == "success"
    assert "Software Engineer" in result["clean_text"]
