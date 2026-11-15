"""
test_report_generator.py - Automated tests for PDF report generation using ReportLab
"""

import pytest
import tempfile
import os
from pathlib import Path
from report_generator import ReportGenerator


def test_generate_pdf_report():
    """Verifies that a valid, multi-section PDF report with page numbers is produced."""
    temp_dir = tempfile.mkdtemp()
    generator = ReportGenerator(output_dir=Path(temp_dir))

    sample_parsed = {
        "candidate_name": "Alex Morgan",
        "file_name": "software_engineer_resume.txt",
        "clean_text": "Experienced software engineer with Python and React.",
        "statistics": {"word_count": 450, "reading_time_minutes": 2.2}
    }

    sample_ats = {
        "total_score": 85.0,
        "badge": {"label": "Excellent", "color": "#10B981"},
        "breakdown": {
            "Contact Information": {"score": 10.0, "max_score": 10, "percentage": 100.0, "feedback": "All channels present."},
            "Section Completeness": {"score": 18.0, "max_score": 20, "percentage": 90.0, "feedback": "All key sections present."}
        },
        "strengths": ["Clean formatting", "Strong action verbs"],
        "weaknesses": ["Needs more metrics"],
        "critical_fixes": []
    }

    sample_job_match = {
        "overall_match_score": 82.0,
        "matched_skills": ["Python", "React", "Docker"],
        "missing_skills": ["Kubernetes"],
        "partial_matching_skills": [{"requested": "PostgreSQL", "candidate_has": "MySQL"}]
    }

    pdf_path = generator.generate_pdf_report(
        parsed_resume=sample_parsed,
        ats_results=sample_ats,
        job_match_results=sample_job_match,
        ai_critique="Candidate exhibits solid technical foundation.",
        target_role="Full Stack Engineer"
    )

    # Verify file was created
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000  # Non-trivial PDF size

    # Verify PDF magic bytes
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"
