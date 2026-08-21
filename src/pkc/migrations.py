from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .app import ConnectionAdapter, KnowledgeStore


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path
    checksum: str


class MigrationError(RuntimeError):
    pass


def default_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "sql" / "migrations"


class MigrationRunner:
    def __init__(self, store: KnowledgeStore, migrations_dir: Path):
        self.store = store
        self.migrations_dir = migrations_dir

    def apply(self) -> list[str]:
        applied: list[str] = []
        for migration in self.pending():
            with self.store.connect() as conn:
                self._ensure_ledger(conn)
                conn.executescript(migration.path.read_text(encoding="utf-8"))
                conn.execute(
                    "INSERT INTO schema_migrations (version, checksum, applied_at) VALUES (?, ?, ?)",
                    (migration.version, migration.checksum, self._now_iso()),
                )
            applied.append(migration.version)
        return applied

    def pending(self) -> list[Migration]:
        migrations = self._discover()
        with self.store.connect() as conn:
            applied = self._applied_checksums(conn)
        for migration in migrations:
            if migration.version in applied and applied[migration.version] != migration.checksum:
                raise MigrationError(
                    f"Applied migration {migration.version} has a different checksum; "
                    "do not edit applied migrations."
                )
        return [migration for migration in migrations if migration.version not in applied]

    @staticmethod
    def _applied_checksums(conn: ConnectionAdapter) -> dict[str, str]:
        if conn.dialect == "sqlite":
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                ("schema_migrations",),
            ).fetchone()
        else:
            exists = conn.execute(
                "SELECT to_regclass('public.schema_migrations') AS name"
            ).fetchone()
        if not exists:
            return {}
        if conn.dialect == "postgresql" and exists["name"] is None:
            return {}
        rows = conn.execute(
            "SELECT version, checksum FROM schema_migrations"
        ).fetchall()
        return {row["version"]: row["checksum"] for row in rows}

    def _discover(self) -> list[Migration]:
        if not self.migrations_dir.is_dir():
            raise MigrationError(f"Migration directory does not exist: {self.migrations_dir}")
        migrations: list[Migration] = []
        for path in sorted(self.migrations_dir.glob("*.sql")):
            text = path.read_bytes()
            migrations.append(
                Migration(
                    version=path.stem,
                    path=path,
                    checksum=hashlib.sha256(text).hexdigest(),
                )
            )
        versions = [migration.version for migration in migrations]
        if len(versions) != len(set(versions)):
            raise MigrationError("Migration versions must be unique")
        return migrations

    @staticmethod
    def _ensure_ledger(conn: ConnectionAdapter) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")
