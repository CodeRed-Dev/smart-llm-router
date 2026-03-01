"""
Storage Module

Handles persistent storage of metrics and request logs using SQLite.
"""

import sqlite3
import json
from typing import List, Dict, Any
from datetime import datetime
from app.config import settings

class MetricsStorage:
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT UNIQUE,
                    timestamp TEXT,
                    route TEXT,
                    model_used TEXT,
                    fallback_used BOOLEAN,
                    latency_ms REAL,
                    llm_latency_ms REAL,
                    judge_latency_ms REAL,
                    cache_hit BOOLEAN,
                    cost_units REAL,
                    judge_correctness INTEGER,
                    judge_completeness INTEGER,
                    judge_format_ok BOOLEAN,
                    judge_hallucination_risk INTEGER,
                    judge_should_fallback BOOLEAN,
                    judge_notes TEXT,
                    error_message TEXT
                )
            """)
            conn.commit()

    def save_request(self, trace_id: str, data: Dict[str, Any]):
        """Save a request record to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO requests (
                    trace_id, timestamp, route, model_used, fallback_used,
                    latency_ms, llm_latency_ms, judge_latency_ms, cache_hit, cost_units,
                    judge_correctness, judge_completeness, judge_format_ok,
                    judge_hallucination_risk, judge_should_fallback, judge_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace_id,
                datetime.now().isoformat(),
                data.get("route"),
                data.get("model_used"),
                data.get("fallback_used", False),
                data.get("latency_ms"),
                data.get("llm_latency_ms"),
                data.get("judge_latency_ms"),
                data.get("cache_hit", False),
                data.get("cost_units"),
                data["judge"].get("correctness"),
                data["judge"].get("completeness"),
                data["judge"].get("format_ok"),
                data["judge"].get("hallucination_risk"),
                data["judge"].get("should_fallback"),
                data["judge"].get("notes")
            ))
            conn.commit()

    def save_error(self, trace_id: str, error_message: str):
        """Save an error record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO requests (trace_id, timestamp, error_message)
                VALUES (?, ?, ?)
            """, (trace_id, datetime.now().isoformat(), error_message))
            conn.commit()

    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent request records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM requests
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get aggregated metrics summary."""
        with sqlite3.connect(self.db_path) as conn:
            # Basic aggregations
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_requests,
                    AVG(latency_ms) as avg_latency,
                    AVG(cost_units) as avg_cost,
                    SUM(fallback_used) as total_fallbacks,
                    AVG(judge_correctness) as avg_correctness,
                    COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_count
                FROM requests
                WHERE timestamp >= datetime('now', '-1 hour')
            """)
            row = cursor.fetchone()
            if row:
                return {
                    "total_requests": row[0],
                    "avg_latency_ms": row[1],
                    "avg_cost_units": row[2],
                    "fallback_rate": row[3] / row[0] if row[0] > 0 else 0,
                    "avg_judge_correctness": row[4],
                    "error_rate": row[5] / row[0] if row[0] > 0 else 0
                }
        return {}