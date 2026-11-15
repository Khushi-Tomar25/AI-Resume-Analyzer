"""
test_skill_extractor.py - Unit tests for skill_extractor.py
"""

import pytest
from skill_extractor import extract_skills_from_text, compare_resume_to_jd_skills, SkillExtractor


def test_extract_skills_by_category():
    text = """
    Proficient in Python, TypeScript, and Java.
    Extensive background with React, Node.js, and Django.
    Deployed databases on PostgreSQL and MongoDB.
    Worked with AWS, Docker, Git, and GitHub in an Agile environment.
    Demonstrated strong communication and leadership abilities.
    """
    res = extract_skills_from_text(text)
    skills = res["all_skills"]
    by_cat = res["skills_by_category"]

    # Programming Languages
    assert "python" in by_cat["Programming Languages"]
    assert "typescript" in by_cat["Programming Languages"]
    assert "java" in by_cat["Programming Languages"]

    # Frameworks
    assert "react" in by_cat["Frameworks"]
    assert "django" in by_cat["Frameworks"]

    # Tools
    assert "docker" in by_cat["Tools"]
    assert "git" in by_cat["Tools"]
    assert "github" in by_cat["Tools"]

    # Technical & Domain Skills
    assert "postgresql" in by_cat["Technical & Domain Skills"]
    assert "mongodb" in by_cat["Technical & Domain Skills"]
    assert "aws" in by_cat["Technical & Domain Skills"]

    # Soft skills
    assert "communication" in by_cat["Soft Skills"]
    assert "leadership" in by_cat["Soft Skills"]


def test_custom_skill_dictionary_extension():
    extractor = SkillExtractor()
    extractor.add_custom_skills("Tools", ["figma", "notion"])
    res = extractor.extract_skills("Experienced with Figma for UI design and Notion for notes.")
    assert "figma" in res["skills_by_category"]["Tools"]
    assert "notion" in res["skills_by_category"]["Tools"]


def test_skill_alias_mapping():
    text = "Experience deploying microservices using k8s and postgres, with a frontend in js."
    res = extract_skills_from_text(text)
    skills = res["all_skills"]

    assert "kubernetes" in skills
    assert "postgresql" in skills
    assert "javascript" in skills


def test_no_false_positives_for_short_tokens():
    # 'go' or 'c' shouldn't match arbitrary words like 'going' or 'cat'
    text = "We are going to celebrate and cat is sleeping."
    res = extract_skills_from_text(text)
    skills = res["all_skills"]
    assert "go" not in skills
    assert "c" not in skills


def test_compare_resume_and_jd_skills():
    resume_skills = ["python", "docker", "sql", "git"]
    jd_skills = ["python", "docker", "kubernetes", "aws"]

    comp = compare_resume_to_jd_skills(resume_skills, jd_skills)
    assert "python" in comp["matched_skills"]
    assert "docker" in comp["matched_skills"]
    assert "kubernetes" in comp["missing_skills"]
    assert "aws" in comp["missing_skills"]
    assert "sql" in comp["additional_skills"]
    assert comp["match_ratio"] == 50.0
