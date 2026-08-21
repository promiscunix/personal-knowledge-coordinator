from pkc.cli import main


def test_migrate_check_reports_pending_without_applying(tmp_path, capsys):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_create_example.sql").write_text(
        "CREATE TABLE example_records (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    database = tmp_path / "knowledge.sqlite3"

    exit_code = main(
        [
            "--db",
            str(database),
            "migrate",
            "--check",
            "--migrations-dir",
            str(migrations),
        ]
    )

    assert exit_code == 0
    assert "pending: 001_create_example" in capsys.readouterr().out
