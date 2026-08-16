from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TASK_OPEN_STATUSES = ("captured", "classified", "queued", "working", "blocked", "waiting_on_user", "ready_for_review")


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def new_id() -> str:
    return str(uuid.uuid4())


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return None if row is None else dict(row)


@dataclass
class CaptureResult:
    capture_id: str
    observation_ids: list[str] = field(default_factory=list)
    task_ids: list[str] = field(default_factory=list)
    conversation_ids: list[str] = field(default_factory=list)
    commitment_ids: list[str] = field(default_factory=list)


class KnowledgeStore:
    """Small SQLite-backed prototype store.

    The first production target is PostgreSQL. This class deliberately keeps SQL
    simple and explicit so the schema can be lifted into PostgreSQL migrations
    while tests and local demos remain cheap and disposable.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def insert_raw_capture(
        self,
        raw_text: str,
        *,
        source_type: str,
        privacy_scope: str,
        captured_by: str,
        source_ref: str | None = None,
        source_vault: str | None = None,
    ) -> str:
        capture_id = new_id()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO raw_captures
                    (id, raw_text, source_type, source_ref, source_vault, captured_at, captured_by, privacy_scope)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (capture_id, raw_text, source_type, source_ref, source_vault, now_iso(), captured_by, privacy_scope),
            )
            self._event(conn, "raw_capture", capture_id, "captured", "Raw input captured", captured_by)
        return capture_id

    def ensure_project(self, slug: str, name: str) -> str:
        project_id = new_id()
        with self.connect() as conn:
            row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
            if row:
                return row["id"]
            conn.execute("INSERT INTO projects (id, slug, name, created_at) VALUES (?, ?, ?, ?)", (project_id, slug, name, now_iso()))
            self._event(conn, "project", project_id, "created", f"Project {slug} created", "coordinator")
        return project_id

    def ensure_person(self, display_name: str) -> str:
        person_id = new_id()
        normalized = display_name.strip().lower()
        with self.connect() as conn:
            row = conn.execute("SELECT id FROM people WHERE normalized_name = ?", (normalized,)).fetchone()
            if row:
                return row["id"]
            conn.execute(
                "INSERT INTO people (id, display_name, normalized_name, created_at) VALUES (?, ?, ?, ?)",
                (person_id, display_name.strip(), normalized, now_iso()),
            )
            self._event(conn, "person", person_id, "created", f"Person {display_name.strip()} created", "coordinator")
        return person_id

    def create_observation(
        self,
        *,
        summary: str,
        kind: str,
        privacy_scope: str,
        source_capture_id: str,
        project_id: str | None = None,
        confidence: float = 0.75,
        verified: bool = False,
        agent: str = "coordinator",
    ) -> str:
        observation_id = new_id()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO observations
                    (id, summary, kind, privacy_scope, project_id, source_capture_id, confidence, verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (observation_id, summary, kind, privacy_scope, project_id, source_capture_id, confidence, int(verified), now_iso()),
            )
            self._event(conn, "observation", observation_id, "created", summary, agent)
        return observation_id

    def create_task(
        self,
        *,
        title: str,
        description: str,
        privacy_scope: str,
        source_capture_id: str,
        project_id: str | None = None,
        assigned_agent: str | None = None,
        status: str = "captured",
        agent: str = "coordinator",
    ) -> str:
        task_id = new_id()
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks
                    (id, title, description, status, privacy_scope, project_id, source_capture_id,
                     assigned_agent, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, title, description, status, privacy_scope, project_id, source_capture_id, assigned_agent, timestamp, timestamp),
            )
            self._event(conn, "task", task_id, "created", title, agent)
            if assigned_agent:
                self._event(conn, "task", task_id, "assigned", f"Assigned to {assigned_agent}", agent)
        return task_id

    def create_conversation(
        self,
        *,
        person_id: str,
        issue: str,
        attributed_explanation: str,
        privacy_scope: str,
        source_capture_id: str,
        agent: str = "coordinator",
    ) -> str:
        conversation_id = new_id()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations
                    (id, person_id, issue, attributed_explanation, privacy_scope, source_capture_id, occurred_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (conversation_id, person_id, issue, attributed_explanation, privacy_scope, source_capture_id, now_iso(), now_iso()),
            )
            self._event(conn, "conversation", conversation_id, "created", f"Conversation about {issue}", agent)
        return conversation_id

    def create_commitment(
        self,
        *,
        person_id: str,
        summary: str,
        privacy_scope: str,
        source_capture_id: str,
        agent: str = "coordinator",
    ) -> str:
        commitment_id = new_id()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO commitments
                    (id, person_id, summary, status, privacy_scope, source_capture_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (commitment_id, person_id, summary, "captured", privacy_scope, source_capture_id, now_iso()),
            )
            self._event(conn, "commitment", commitment_id, "created", summary, agent)
        return commitment_id

    def get_raw_capture(self, capture_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM raw_captures WHERE id = ?", (capture_id,)).fetchone())  # type: ignore[return-value]

    def get_task(self, task_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT tasks.*, projects.slug AS project_slug
                FROM tasks LEFT JOIN projects ON projects.id = tasks.project_id
                WHERE tasks.id = ?
                """,
                (task_id,),
            ).fetchone()
            return row_to_dict(row)  # type: ignore[return-value]

    def get_observation(self, observation_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM observations WHERE id = ?", (observation_id,)).fetchone())  # type: ignore[return-value]

    def get_person_by_name(self, display_name: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM people WHERE normalized_name = ?", (display_name.lower(),)).fetchone())

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone())  # type: ignore[return-value]

    def get_commitment(self, commitment_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            return row_to_dict(conn.execute("SELECT * FROM commitments WHERE id = ?", (commitment_id,)).fetchone())  # type: ignore[return-value]

    def inbox(self) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in TASK_OPEN_STATUSES)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT tasks.id, tasks.title, tasks.status, tasks.assigned_agent, tasks.privacy_scope,
                       projects.slug AS project_slug, raw_captures.raw_text, tasks.created_at
                FROM tasks
                JOIN raw_captures ON raw_captures.id = tasks.source_capture_id
                LEFT JOIN projects ON projects.id = tasks.project_id
                WHERE tasks.status IN ({placeholders})
                ORDER BY tasks.created_at ASC
                """,
                TASK_OPEN_STATUSES,
            ).fetchall()
            return [dict(row) for row in rows]

    def activity_for(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM activity_events WHERE entity_type = ? AND entity_id = ? ORDER BY occurred_at, rowid",
                (entity_type, entity_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def _event(self, conn: sqlite3.Connection, entity_type: str, entity_id: str, event_type: str, message: str, actor: str) -> None:
        conn.execute(
            """
            INSERT INTO activity_events (id, entity_type, entity_id, event_type, message, actor, occurred_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id(), entity_type, entity_id, event_type, message, actor, now_iso(), json.dumps({})),
        )


class CaptureService:
    def __init__(self, store: KnowledgeStore, agent_name: str = "coordinator"):
        self.store = store
        self.agent_name = agent_name

    def capture(self, raw_text: str, *, source_type: str = "direct_input") -> CaptureResult:
        text = raw_text.strip()
        classification = self._classify(text)
        capture_id = self.store.insert_raw_capture(
            text,
            source_type=source_type,
            privacy_scope=classification["privacy_scope"],
            captured_by=self.agent_name,
        )
        result = CaptureResult(capture_id=capture_id)

        if classification["kind"] == "parts_advisor_ui":
            project_id = self.store.ensure_project("part-suite", "part-suite")
            result.observation_ids.append(
                self.store.create_observation(
                    summary="User reported Parts Advisor UI concerns in part-suite.",
                    kind="ui_ux_issue",
                    privacy_scope="project:part-suite",
                    project_id=project_id,
                    source_capture_id=capture_id,
                    agent=self.agent_name,
                )
            )
            result.task_ids.append(
                self.store.create_task(
                    title="Inspect Parts Advisor UI concerns",
                    description="Review the Parts Advisor page in part-suite and propose UI/UX improvements. Preserve the user's original wording via source_capture_id.",
                    privacy_scope="project:part-suite",
                    project_id=project_id,
                    source_capture_id=capture_id,
                    assigned_agent="developer",
                    agent=self.agent_name,
                )
            )
        elif classification["kind"] == "tom_callbacks_conversation":
            person_id = self.store.ensure_person("Tom")
            result.conversation_ids.append(
                self.store.create_conversation(
                    person_id=person_id,
                    issue="missing callbacks",
                    attributed_explanation="Tom says he gets distracted when the counter gets busy.",
                    privacy_scope="management-private",
                    source_capture_id=capture_id,
                    agent=self.agent_name,
                )
            )
            result.commitment_ids.append(
                self.store.create_commitment(
                    person_id=person_id,
                    summary="Tom will check the callback list at 11 and 3.",
                    privacy_scope="management-private",
                    source_capture_id=capture_id,
                    agent=self.agent_name,
                )
            )
        else:
            result.observation_ids.append(
                self.store.create_observation(
                    summary=text,
                    kind="thought",
                    privacy_scope=classification["privacy_scope"],
                    source_capture_id=capture_id,
                    confidence=0.5,
                    agent=self.agent_name,
                )
            )
        return result

    def _classify(self, text: str) -> dict[str, str]:
        lower = text.lower()
        if "part-suite" in lower and "parts advisor" in lower and re.search(r"\b(ui|page|clutter|layout|look)\b", lower):
            return {"kind": "parts_advisor_ui", "privacy_scope": "project:part-suite"}
        if lower.startswith("talked to tom") and "callbacks" in lower:
            return {"kind": "tom_callbacks_conversation", "privacy_scope": "management-private"}
        return {"kind": "thought", "privacy_scope": "personal"}


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_captures (
    id TEXT PRIMARY KEY,
    raw_text TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT,
    source_vault TEXT,
    captured_at TEXT NOT NULL,
    captured_by TEXT NOT NULL,
    privacy_scope TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    kind TEXT NOT NULL,
    privacy_scope TEXT NOT NULL,
    project_id TEXT REFERENCES projects(id),
    source_capture_id TEXT NOT NULL REFERENCES raw_captures(id),
    confidence REAL NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES people(id),
    issue TEXT NOT NULL,
    attributed_explanation TEXT,
    privacy_scope TEXT NOT NULL,
    source_capture_id TEXT NOT NULL REFERENCES raw_captures(id),
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS commitments (
    id TEXT PRIMARY KEY,
    person_id TEXT REFERENCES people(id),
    summary TEXT NOT NULL,
    status TEXT NOT NULL,
    privacy_scope TEXT NOT NULL,
    source_capture_id TEXT NOT NULL REFERENCES raw_captures(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    privacy_scope TEXT NOT NULL,
    project_id TEXT REFERENCES projects(id),
    source_capture_id TEXT NOT NULL REFERENCES raw_captures(id),
    assigned_agent TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_events (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    actor TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_captures_scope ON raw_captures(privacy_scope);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_scope ON tasks(privacy_scope);
CREATE INDEX IF NOT EXISTS idx_activity_entity ON activity_events(entity_type, entity_id);
"""
