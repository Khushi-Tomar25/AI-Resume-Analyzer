"""
test_database.py - Automated tests for SQLite database operations
"""

import pytest
import tempfile
import os
from pathlib import Path
from database import DatabaseManager


@pytest.fixture
def temp_db():
    """Creates an isolated temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    yield db
    # Safe cleanup on Windows
    try:
        import gc
        gc.collect()
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_database_init(temp_db):
    """Verifies tables are created with user_id column."""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r["name"] for r in cursor.fetchall()]
        assert "analyses" in tables
        assert "saved_jobs" in tables


def test_save_and_retrieve_analysis(temp_db):
    """Tests inserting an analysis record and fetching it."""
    record_id = temp_db.save_analysis(
        candidate_name="Jane Developer",
        filename="jane_resume.pdf",
        email="jane@example.com",
        ats_score=84.5,
        match_score=78.0,
        target_role="Frontend Engineer",
        summary_data={"skills": ["React", "TypeScript"]},
        ai_feedback="Strong profile."
    )
    assert record_id > 0

    record = temp_db.get_analysis_by_id(record_id)
    assert record is not None
    assert record["candidate_name"] == "Jane Developer"
    assert record["ats_score"] == 84.5
    assert record["summary"]["skills"] == ["React", "TypeScript"]


def test_delete_individual_analysis(temp_db):
    """Tests deleting a specific analysis record."""
    id1 = temp_db.save_analysis(candidate_name="Alice", filename="a.pdf", email="", ats_score=80.0)
    id2 = temp_db.save_analysis(candidate_name="Bob", filename="b.pdf", email="", ats_score=85.0)

    # Delete id1
    deleted = temp_db.delete_analysis(id1)
    assert deleted is True

    # id1 should be gone, id2 should remain
    assert temp_db.get_analysis_by_id(id1) is None
    assert temp_db.get_analysis_by_id(id2) is not None


def test_analytics_stats(temp_db):
    """Tests summary statistics calculation."""
    temp_db.save_analysis(candidate_name="Candidate 1", filename="c1.pdf", email="", ats_score=70.0, match_score=60.0)
    temp_db.save_analysis(candidate_name="Candidate 2", filename="c2.pdf", email="", ats_score=90.0, match_score=80.0)

    stats = temp_db.get_analytics_stats()
    assert stats["total_scans"] == 2
    assert stats["avg_ats_score"] == 80.0
    assert stats["max_ats_score"] == 90.0
    assert stats["min_ats_score"] == 70.0
    assert stats["avg_match_score"] == 70.0


def test_clear_all_history(temp_db):
    """Tests wiping history records."""
    temp_db.save_analysis(candidate_name="Test", filename="t.pdf", email="", ats_score=75.0)
    temp_db.clear_all_history()
    recent = temp_db.get_recent_analyses()
    assert len(recent) == 0
