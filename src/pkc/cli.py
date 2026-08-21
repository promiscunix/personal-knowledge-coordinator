from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .app import CaptureService, KnowledgeStore
from .migrations import MigrationRunner, default_migrations_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pkc", description="Personal knowledge coordinator prototype")
    parser.add_argument("--db", default=None, help="SQLite DB path. Omit to use PKC_DATABASE_URL or data/knowledge.sqlite3.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Initialize the prototype database")

    migrate = sub.add_parser("migrate", help="Apply ordered database migrations")
    migrate.add_argument("--check", action="store_true", help="List pending migrations without applying them")
    migrate.add_argument(
        "--migrations-dir",
        type=Path,
        default=default_migrations_dir(),
        help="Directory containing ordered .sql migration files",
    )

    capture = sub.add_parser("capture", help="Capture a natural-language input")
    capture.add_argument("text", help="Raw text to capture verbatim")
    capture.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    inbox = sub.add_parser("inbox", help="Show open tasks")
    inbox.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    show = sub.add_parser("show-task", help="Show a task and its activity")
    show.add_argument("task_id")
    show.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = KnowledgeStore.from_env(Path(args.db) if args.db else None)

    if args.command == "migrate":
        runner = MigrationRunner(store, args.migrations_dir)
        if args.check:
            pending = runner.pending()
            if not pending:
                print("No pending migrations.")
            for migration in pending:
                print(f"pending: {migration.version}")
            return 0
        for version in runner.apply():
            print(f"applied: {version}")
        return 0

    if args.command == "init-db":
        store.initialize()
        target = os.environ.get("PKC_DATABASE_URL") or str(store.db_path)
        print(f"initialized {target}")
        return 0

    store.initialize()
    if args.command == "capture":
        result = CaptureService(store).capture(args.text)
        payload = {
            "capture_id": result.capture_id,
            "task_ids": result.task_ids,
            "observation_ids": result.observation_ids,
            "conversation_ids": result.conversation_ids,
            "commitment_ids": result.commitment_ids,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"captured: {result.capture_id}")
            for task_id in result.task_ids:
                print(f"task: {task_id}")
        return 0

    if args.command == "inbox":
        rows = store.inbox()
        if args.json:
            print(json.dumps(rows, indent=2, sort_keys=True))
        else:
            if not rows:
                print("Inbox is empty.")
            for row in rows:
                project = row["project_slug"] or row["privacy_scope"]
                print(f"{row['id']} [{row['status']}] {project}: {row['title']} -> {row['assigned_agent'] or 'unassigned'}")
        return 0

    if args.command == "show-task":
        task = store.get_task(args.task_id)
        events = store.activity_for("task", args.task_id)
        payload = {"task": task, "activity": events}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"{task['title']} ({task['status']})")
            print(task["description"])
            for event in events:
                print(f"- {event['occurred_at']} {event['event_type']}: {event['message']}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
