# english_agent_core.py
# Python 3.10+
# 通用英语学习 Agent 支持库

import sqlite3
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

DB_PATH = Path("english_agent.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        user_id TEXT PRIMARY KEY,
        level TEXT DEFAULT 'A2',
        goal TEXT DEFAULT '',
        daily_minutes INTEGER DEFAULT 10,
        interests TEXT DEFAULT '[]',
        weak_points TEXT DEFAULT '[]',
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS learning_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        agent_name TEXT,
        event_type TEXT,
        content TEXT,
        result TEXT,
        score REAL,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS review_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        agent_name TEXT,
        item_type TEXT,
        item TEXT,
        explanation TEXT,
        difficulty INTEGER DEFAULT 2,
        interval_days INTEGER DEFAULT 1,
        ease_factor REAL DEFAULT 2.5,
        repetitions INTEGER DEFAULT 0,
        next_review_at TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        agent_name TEXT,
        trigger_time TEXT,
        frequency TEXT,
        task_template TEXT,
        enabled INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def upsert_profile(
    user_id: str,
    level: str = "A2",
    goal: str = "",
    daily_minutes: int = 10,
    interests: Optional[List[str]] = None,
    weak_points: Optional[List[str]] = None
):
    interests = interests or []
    weak_points = weak_points or []

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO user_profile
    (user_id, level, goal, daily_minutes, interests, weak_points, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        level=excluded.level,
        goal=excluded.goal,
        daily_minutes=excluded.daily_minutes,
        interests=excluded.interests,
        weak_points=excluded.weak_points,
        updated_at=excluded.updated_at
    """, (
        user_id,
        level,
        goal,
        daily_minutes,
        json.dumps(interests, ensure_ascii=False),
        json.dumps(weak_points, ensure_ascii=False),
        now_iso(),
        now_iso()
    ))
    conn.commit()
    conn.close()


def get_profile(user_id: str) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT * FROM user_profile WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    if not row:
        return {
            "user_id": user_id,
            "level": "A2",
            "goal": "",
            "daily_minutes": 10,
            "interests": [],
            "weak_points": []
        }

    return {
        "user_id": row["user_id"],
        "level": row["level"],
        "goal": row["goal"],
        "daily_minutes": row["daily_minutes"],
        "interests": json.loads(row["interests"] or "[]"),
        "weak_points": json.loads(row["weak_points"] or "[]")
    }


def log_event(
    user_id: str,
    agent_name: str,
    event_type: str,
    content: str,
    result: str = "",
    score: Optional[float] = None
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO learning_events
    (user_id, agent_name, event_type, content, result, score, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        agent_name,
        event_type,
        content,
        result,
        score,
        now_iso()
    ))
    conn.commit()
    conn.close()


def add_review_item(
    user_id: str,
    agent_name: str,
    item_type: str,
    item: str,
    explanation: str = "",
    difficulty: int = 2
):
    conn = get_conn()
    cur = conn.cursor()
    next_review_at = datetime.utcnow() + timedelta(days=1)
    cur.execute("""
    INSERT INTO review_items
    (user_id, agent_name, item_type, item, explanation, difficulty,
     interval_days, ease_factor, repetitions, next_review_at, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        agent_name,
        item_type,
        item,
        explanation,
        difficulty,
        1,
        2.5,
        0,
        next_review_at.isoformat(),
        now_iso(),
        now_iso()
    ))
    conn.commit()
    conn.close()


def get_due_reviews(
    user_id: str,
    agent_name: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    if agent_name:
        rows = cur.execute("""
        SELECT * FROM review_items
        WHERE user_id=? AND agent_name=? AND next_review_at<=?
        ORDER BY next_review_at ASC
        LIMIT ?
        """, (user_id, agent_name, now_iso(), limit)).fetchall()
    else:
        rows = cur.execute("""
        SELECT * FROM review_items
        WHERE user_id=? AND next_review_at<=?
        ORDER BY next_review_at ASC
        LIMIT ?
        """, (user_id, now_iso(), limit)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def sm2_update(review_id: int, quality: int):
    quality = max(0, min(5, quality))

    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT * FROM review_items WHERE id=?",
        (review_id,)
    ).fetchone()

    if not row:
        conn.close()
        return

    ease = row["ease_factor"]
    interval = row["interval_days"]
    reps = row["repetitions"]

    if quality < 3:
        reps = 0
        interval = 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 3
        else:
            interval = math.ceil(interval * ease)

        reps += 1
        ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ease = max(1.3, ease)

    next_review_at = datetime.utcnow() + timedelta(days=interval)

    cur.execute("""
    UPDATE review_items
    SET interval_days=?, ease_factor=?, repetitions=?, next_review_at=?, updated_at=?
    WHERE id=?
    """, (
        interval,
        ease,
        reps,
        next_review_at.isoformat(),
        now_iso(),
        review_id
    ))

    conn.commit()
    conn.close()


def get_recent_errors(user_id: str, agent_name: str, days: int = 7) -> List[Dict[str, Any]]:
    since = datetime.utcnow() - timedelta(days=days)
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("""
    SELECT * FROM learning_events
    WHERE user_id=? AND agent_name=? AND event_type='error'
    AND created_at>=?
    ORDER BY created_at DESC
    """, (user_id, agent_name, since.isoformat())).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_daily_task(profile: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    level = profile.get("level", "A2")
    minutes = profile.get("daily_minutes", 10)
    interests = profile.get("interests", [])

    task_types = ["new_input", "review", "mini_quiz", "output_practice"]
    if minutes <= 5:
        selected = ["review", "mini_quiz"]
    elif minutes <= 15:
        selected = ["new_input", "review", "mini_quiz"]
    else:
        selected = task_types

    return {
        "agent_name": agent_name,
        "level": level,
        "estimated_minutes": minutes,
        "task_flow": selected,
        "interest_hint": random.choice(interests) if interests else "daily life",
        "created_at": now_iso()
    }


def weekly_report(user_id: str, agent_name: Optional[str] = None) -> Dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=7)
    conn = get_conn()
    cur = conn.cursor()

    if agent_name:
        rows = cur.execute("""
        SELECT * FROM learning_events
        WHERE user_id=? AND agent_name=? AND created_at>=?
        """, (user_id, agent_name, since.isoformat())).fetchall()
    else:
        rows = cur.execute("""
        SELECT * FROM learning_events
        WHERE user_id=? AND created_at>=?
        """, (user_id, since.isoformat())).fetchall()

    conn.close()

    total = len(rows)
    errors = sum(1 for r in rows if r["event_type"] == "error")
    correct = sum(1 for r in rows if r["event_type"] == "correct")

    return {
        "total_events": total,
        "errors": errors,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1) if total > 0 else 0
    }


init_db()
