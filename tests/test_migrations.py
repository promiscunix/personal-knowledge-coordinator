import pytest

from pkc.app import KnowledgeStore
from pkc.migrations import MigrationError, MigrationRunner


def test_apply_runs_pending_migration_and_records_its_checksum(tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_create_example.sql").write_text(
        "CREATE TABLE example_records (id TEXT PRIMARY KEY, value TEXT NOT NULL);\n",
        encoding="utf-8",
    )
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")

    applied = MigrationRunner(store, migrations).apply()

    assert applied == ["001_create_example"]
    with store.connect() as conn:
        row = conn.execute(
            "SELECT version, checksum FROM schema_migrations WHERE version = ?",
            ("001_create_example",),
        ).fetchone()
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("example_records",),
        ).fetchone()
    assert row is not None
    assert row["checksum"]
    assert table is not None


def test_pending_lists_migrations_without_creating_the_ledger(tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_create_example.sql").write_text(
        "CREATE TABLE example_records (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")

    pending = MigrationRunner(store, migrations).pending()

    assert [migration.version for migration in pending] == ["001_create_example"]
    with store.connect() as conn:
        ledger = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("schema_migrations",),
        ).fetchone()
    assert ledger is None


def test_pending_rejects_an_edited_applied_migration(tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    migration = migrations / "001_create_example.sql"
    migration.write_text("CREATE TABLE example_records (id TEXT PRIMARY KEY);\n", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    runner = MigrationRunner(store, migrations)
    runner.apply()
    migration.write_text("CREATE TABLE example_records (id TEXT PRIMARY KEY, value TEXT);\n", encoding="utf-8")

    with pytest.raises(MigrationError, match="different checksum"):
        runner.pending()
