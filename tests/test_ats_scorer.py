"""
test_ats_scorer.py - Unit tests for ats_scorer.py
"""

import pytest
from ats_scorer import calculate_ats_score, ATSScorer
from utils import count_action_verbs, extract_quantified_achievements


def test_action_verbs_counting():
    text = "Architected a scalable API, spearheaded migration, and improved query latency."
    count, verbs = count_action_verbs(text)
    assert count >= 3
    assert "architected" in verbs
    assert "spearheaded" in verbs
    assert "improved" in verbs


def test_quantified_achievements_extraction():
    text = "Increased revenue by 35% and reduced cloud costs by $25,000 for 50,000 users."
    achievements = extract_quantified_achievements(text)
    assert len(achievements) >= 2


def test_ats_score_high_quality_resume():
    parsed_sample = {
        "candidate_name": "Alex Morgan",
        "email": "alex.morgan@example.com",
        "phone": "+1 555-234-5678",
        "links": {
            "linkedin": "https://linkedin.com/in/alexmorgan",
            "github": "https://github.com/alexmorgan"
        },
        "clean_text": """
        Alex Morgan
        alex.morgan@example.com | 555-234-5678
        https://linkedin.com/in/alexmorgan | https://github.com/alexmorgan
        
        EXPERIENCE
        Senior Engineer | TechCorp
        - Architected microservices backend with FastAPI, serving 250,000 users with 99.9% uptime.
        - Reduced API latency by 45% and decreased monthly infrastructure costs by $30,000.
        - Spearheaded Python and React migration across 4 engineering teams.
        - Developed, deployed, engineered, and automated continuous integration pipelines.
        - Optimized queries, eliminated bugs, collaborated with engineers, and improved performance.
        
        EDUCATION
        BS in Computer Science, UC Berkeley.
        
        SKILLS
        Python, JavaScript, TypeScript, React, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, Linux, SQL, MongoDB
        
        PROJECTS
        Built cloud telemetry system.
        
        CERTIFICATIONS
        AWS Certified Solutions Architect
        """,
        "sections": {
            "experience": "Senior Engineer at TechCorp. Architected microservices.",
            "education": "BS in Computer Science, UC Berkeley.",
            "skills": "Python, React, AWS, Docker, Kubernetes, PostgreSQL",
            "projects": "Built cloud telemetry system.",
            "certifications": "AWS Certified Solutions Architect"
        },
        "statistics": {
            "word_count": 450,
            "line_count": 30,
            "reading_time_minutes": 2.2
        }
    }

    results = calculate_ats_score(parsed_sample)
    assert results["total_score"] >= 75
    assert results["badge"]["label"] in ["Good", "Excellent"]
    assert "Section Completeness" in results["breakdown"]
    assert "Contact Information" in results["breakdown"]
    assert len(results["strengths"]) > 0
    assert "methodology_disclaimer" in results
    assert "Workday" in results["methodology_disclaimer"]


def test_ats_score_sparse_resume():
    sparse_sample = {
        "candidate_name": "Test User",
        "email": None,
        "phone": None,
        "links": {},
        "clean_text": "Looking for a job. Worked at store.",
        "sections": {},
        "statistics": {
            "word_count": 10,
            "line_count": 2,
            "reading_time_minutes": 0.1
        }
    }

    results = calculate_ats_score(sparse_sample)
    assert results["total_score"] < 50
    assert results["badge"]["label"] == "Needs Improvement"
    assert len(results["critical_fixes"]) > 0
