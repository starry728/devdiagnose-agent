import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import data_dir


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def uid() -> str:
    return uuid.uuid4().hex


@contextmanager
def db():
    conn = sqlite3.connect(data_dir() / "app.sqlite", timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize():
    with db() as conn:
        conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS workspaces (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sources (
          id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
          path TEXT NOT NULL, content TEXT NOT NULL, kind TEXT NOT NULL,
          package TEXT NOT NULL, version TEXT NOT NULL, sha256 TEXT NOT NULL,
          created_at TEXT NOT NULL, UNIQUE(workspace_id,path,package,version));
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
          question TEXT NOT NULL, mode TEXT NOT NULL, status TEXT NOT NULL,
          max_steps INTEGER NOT NULL, snapshot TEXT NOT NULL, result TEXT,
          error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL REFERENCES tasks(id),
          stage TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL);
        """)
        conn.execute(
            "UPDATE tasks SET status='interrupted',updated_at=? WHERE status IN ('queued','running')",
            (now(),),
        )


def workspace_exists(workspace_id: str) -> bool:
    with db() as conn:
        return conn.execute("SELECT 1 FROM workspaces WHERE id=?", (workspace_id,)).fetchone() is not None


def sources(workspace_id: str) -> list[dict]:
    with db() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM sources WHERE workspace_id=? ORDER BY created_at", (workspace_id,)
            )
        ]


def task(task_id: str) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result.pop("snapshot")
        result["result"] = json.loads(result["result"]) if result["result"] else None
        result["events"] = [
            dict(e)
            for e in conn.execute(
                "SELECT id,stage,message,created_at FROM events WHERE task_id=? ORDER BY id", (task_id,)
            )
        ]
        return result


def event(task_id: str, stage: str, message: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO events(task_id,stage,message,created_at) VALUES (?,?,?,?)",
            (task_id, stage, message[:1000], now()),
        )


def task_update(task_id: str, status: str, *, result=None, error=None):
    with db() as conn:
        conn.execute(
            "UPDATE tasks SET status=?,result=?,error=?,updated_at=? WHERE id=?",
            (status, json.dumps(result, ensure_ascii=False) if result else None, error, now(), task_id),
        )
