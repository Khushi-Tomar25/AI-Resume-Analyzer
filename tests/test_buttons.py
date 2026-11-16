import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import SAMPLE_RESUMES_DIR
from resume_parser import parse_resume
from ats_scorer import calculate_ats_score

def test_dev_resume_button():
    dev_file = SAMPLE_RESUMES_DIR / "software_engineer_resume.txt"
    assert dev_file.exists(), f"Dev resume file missing at {dev_file}"
    p_dev = parse_resume(dev_file.read_bytes(), dev_file.name)
    assert p_dev["parsing_status"] == "success"
    assert p_dev["candidate_name"] == "Alex Morgan"
    ats = calculate_ats_score(p_dev)
    assert ats["total_score"] >= 75
    print(f"Dev Resume parsed: {p_dev['candidate_name']}, Score: {ats['total_score']}/100, Tier: {ats['badge']['label']}")

def test_fresher_resume_button():
    fresh_file = SAMPLE_RESUMES_DIR / "fresher_resume.txt"
    assert fresh_file.exists(), f"Fresher resume file missing at {fresh_file}"
    p_fresh = parse_resume(fresh_file.read_bytes(), fresh_file.name)
    assert p_fresh["parsing_status"] == "success"
    assert p_fresh["candidate_name"] == "Priya Sharma"
    ats = calculate_ats_score(p_fresh)
    assert ats["total_score"] >= 50
    print(f"Fresher Resume parsed: {p_fresh['candidate_name']}, Score: {ats['total_score']}/100, Tier: {ats['badge']['label']}")

def test_home_demo_resume_button():
    demo_file = SAMPLE_RESUMES_DIR / "software_engineer_resume.txt"
    assert demo_file.exists(), f"Demo resume file missing at {demo_file}"
    p_demo = parse_resume(demo_file.read_bytes(), demo_file.name)
    assert p_demo["parsing_status"] == "success"
    assert p_demo["candidate_name"] == "Alex Morgan"
    ats = calculate_ats_score(p_demo)
    assert ats["total_score"] >= 75
    print(f"Demo Resume parsed: {p_demo['candidate_name']}, Score: {ats['total_score']}/100")

if __name__ == "__main__":
    test_dev_resume_button()
    test_fresher_resume_button()
    test_home_demo_resume_button()
    print("ALL THREE BUTTON LOGICS PASSED!")
