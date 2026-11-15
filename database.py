"""
database.py - SQLite Database Management Layer
-----------------------------------------------
Handles persistent storage of resume analysis metadata, ATS scores,
skill audits, and job matching records using lightweight, embedded SQLite.

Privacy & Security Architecture:
- Stores only aggregated metadata and non-sensitive scoring summaries.
- Never stores original raw resume documents or binary files.
- Local database history resides strictly on the computer hosting the app.
- Designed with `user_id` schema support so authentication and multi-user
  isolation can be added in future iterations.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from config import DB_PATH
from utils import safe_json_dumps, safe_json_loads


class DatabaseManager:
    """
    Manages SQLite database connections, schema migrations, and queries.
    """

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Establishes and returns a database connection with dictionary row access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates required tables and indices with future multi-tenant auth support."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Analyses table (includes user_id for future authentication architecture)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT DEFAULT 'local_user',
                    candidate_name TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    email TEXT,
                    ats_score REAL NOT NULL,
                    match_score REAL,
                    target_role TEXT,
                    summary_json TEXT,
                    ai_feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Ensure user_id column exists if migrating an existing database
            cursor.execute("PRAGMA table_info(analyses);")
            columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in columns:
                cursor.execute("ALTER TABLE analyses ADD COLUMN user_id TEXT DEFAULT 'local_user';")

            # Saved Job Descriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT DEFAULT 'local_user',
                    job_title TEXT NOT NULL,
                    company TEXT,
                    jd_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Index for fast timestamp queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analyses_created_at 
                ON analyses(created_at DESC);
            """)
            conn.commit()

    def save_analysis(
        self,
        candidate_name: str,
        filename: str,
        email: Optional[str],
        ats_score: float,
        match_score: Optional[float] = None,
        target_role: Optional[str] = None,
        summary_data: Optional[Dict[str, Any]] = None,
        ai_feedback: Optional[str] = None,
        user_id: str = "local_user"
    ) -> int:
        """
        Inserts a completed resume analysis into the database.
        Stores only computed metrics and safe summary metadata (no raw resume binaries).
        Returns the generated record ID.
        """
        summary_json = safe_json_dumps(summary_data or {})
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analyses (
                    user_id, candidate_name, filename, email, ats_score, 
                    match_score, target_role, summary_json, ai_feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id or "local_user",
                candidate_name or "Candidate",
                filename or "resume.txt",
                email or "",
                round(float(ats_score), 1),
                round(float(match_score), 1) if match_score is not None else None,
                target_role or "General",
                summary_json,
                ai_feedback or ""
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_analyses(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves previous analyses ordered by date (optional user_id filtering)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    SELECT id, user_id, candidate_name, filename, email, ats_score, 
                           match_score, target_role, summary_json, ai_feedback, created_at
                    FROM analyses
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT id, user_id, candidate_name, filename, email, ats_score, 
                           match_score, target_role, summary_json, ai_feedback, created_at
                    FROM analyses
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()

            results = []
            for r in rows:
                row_dict = dict(r)
                row_dict["summary"] = safe_json_loads(row_dict.get("summary_json", "{}"))
                results.append(row_dict)
            return results

    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a specific historical analysis record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analyses WHERE id = ?
            """, (analysis_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["summary"] = safe_json_loads(res.get("summary_json", "{}"))
            return res

    def delete_analysis(self, analysis_id: int) -> bool:
        """Deletes an individual analysis record by its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_history(self, user_id: Optional[str] = None) -> bool:
        """Clears records from the analyses table (optionally scoped to user_id)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("DELETE FROM analyses WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("DELETE FROM analyses;")
            conn.commit()
            return True

    def get_analytics_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates statistical metrics across historical scans."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    COUNT(*) as total_scans,
                    AVG(ats_score) as avg_ats_score,
                    MAX(ats_score) as max_ats_score,
                    MIN(ats_score) as min_ats_score,
                    AVG(match_score) as avg_match_score
                FROM analyses
            """
            params = ()
            if user_id:
                query += " WHERE user_id = ?"
                params = (user_id,)

            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row or row["total_scans"] == 0:
                return {
                    "total_scans": 0,
                    "avg_ats_score": 0.0,
                    "max_ats_score": 0.0,
                    "min_ats_score": 0.0,
                    "avg_match_score": 0.0
                }

            return {
                "total_scans": row["total_scans"],
                "avg_ats_score": round(row["avg_ats_score"] or 0.0, 1),
                "max_ats_score": round(row["max_ats_score"] or 0.0, 1),
                "min_ats_score": round(row["min_ats_score"] or 0.0, 1),
                "avg_match_score": round(row["avg_match_score"] or 0.0, 1) if row["avg_match_score"] else 0.0
            }


_db_manager = DatabaseManager()

def get_database() -> DatabaseManager:
    """Returns singleton DatabaseManager instance."""
    return _db_manager
