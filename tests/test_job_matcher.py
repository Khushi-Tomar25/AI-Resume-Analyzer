"""
test_job_matcher.py - Unit tests for job_matcher.py
"""

import pytest
from job_matcher import match_resume_to_job, JobMatcher


def test_tfidf_similarity():
    matcher = JobMatcher()
    resume_text = "Proficient Python and React developer with experience in AWS cloud and Docker containers."
    jd_similar = "Looking for a Python and React engineer experienced with AWS and Docker infrastructure."
    jd_different = "Hiring an experienced registered nurse with ICU patient care certifications."

    sim_high = matcher.compute_tfidf_similarity(resume_text, jd_similar)
    sim_low = matcher.compute_tfidf_similarity(resume_text, jd_different)

    assert sim_high > sim_low
    assert sim_high > 15.0


def test_job_match_full_pipeline():
    resume_text = """
    Full Stack Developer with 4 years of experience.
    Proficient in Python, JavaScript, React, FastAPI, MySQL, and Docker.
    Built microservices on AWS with Git CI/CD.
    """
    jd_text = """
    We are seeking a Senior Full Stack Engineer with 3+ years experience.
    Requirements:
    - 3+ years with Python and React
    - Hands-on experience with PostgreSQL and Docker
    - Knowledge of Kubernetes and Terraform is a huge plus
    """

    results = match_resume_to_job(resume_text, jd_text)
    assert "overall_match_score" in results
    assert results["overall_match_score"] > 25.0
    
    # Check that Python, React, Docker are in matched_skills
    matched = [s.lower() for s in results["matched_skills"]]
    assert "python" in matched
    assert "react" in matched
    assert "docker" in matched

    # Partial match check: candidate has MySQL, JD asks for PostgreSQL
    partials = [p["requested"].lower() for p in results.get("partial_matching_skills", [])]
    assert "postgresql" in partials

    # Experience requirement alignment
    exp = results.get("experience_alignment", {})
    assert "3" in exp.get("required_experience", "")

    # Methodology explanation present
    assert "methodology_explanation" in results


def test_job_match_empty_jd():
    resume_text = "Python engineer"
    results = match_resume_to_job(resume_text, "")
    assert "error" in results
