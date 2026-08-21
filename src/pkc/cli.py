from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .app import CaptureService, KnowledgeStore
from .migrations import MigrationRunner, default_migrations_dir


def json_output(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


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

    quote = sub.add_parser("quote", help="Capture and retrieve quotes")
    quote_sub = quote.add_subparsers(dest="quote_command", required=True)
    quote_add = quote_sub.add_parser("add")
    quote_add.add_argument("--text", required=True)
    quote_add.add_argument("--speaker")
    quote_add.add_argument("--source")
    quote_add.add_argument("--locator")
    quote_add.add_argument("--attribution-confidence", type=int, default=50)
    quote_add.add_argument("--attribution-status", default="unknown")
    quote_add.add_argument("--privacy-scope", default="personal")
    quote_add.add_argument("--raw-text")
    quote_add.add_argument("--json", action="store_true")
    quote_list = quote_sub.add_parser("list")
    quote_list.add_argument("--query", default="")
    quote_list.add_argument("--limit", type=int, default=20)
    quote_list.add_argument("--json", action="store_true")
    quote_show = quote_sub.add_parser("show")
    quote_show.add_argument("quote_id")
    quote_show.add_argument("--json", action="store_true")

    lesson = sub.add_parser("lesson", help="Capture and retrieve life lessons")
    lesson_sub = lesson.add_subparsers(dest="lesson_command", required=True)
    lesson_add = lesson_sub.add_parser("add")
    lesson_add.add_argument("--text", required=True)
    lesson_add.add_argument("--privacy-scope", default="personal")
    lesson_add.add_argument("--raw-text")
    lesson_add.add_argument("--json", action="store_true")
    lesson_list = lesson_sub.add_parser("list")
    lesson_list.add_argument("--query", default="")
    lesson_list.add_argument("--limit", type=int, default=20)
    lesson_list.add_argument("--json", action="store_true")
    lesson_show = lesson_sub.add_parser("show")
    lesson_show.add_argument("lesson_id")
    lesson_show.add_argument("--json", action="store_true")

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
    if args.command == "quote":
        service = CaptureService(store)
        if args.quote_command == "add":
            result = service.capture_quote(exact_text=args.text, speaker=args.speaker, source_label=args.source, source_locator=args.locator, attribution_confidence=args.attribution_confidence, attribution_status=args.attribution_status, privacy_scope=args.privacy_scope, raw_text=args.raw_text)
            payload = {"capture_id": result.capture_id, "quote_id": result.record_id}
        elif args.quote_command == "list":
            payload = store.list_quotes(args.query, args.limit)
        else:
            payload = store.get_quote(args.quote_id)
        print(json_output(payload))
        return 0
    if args.command == "lesson":
        service = CaptureService(store)
        if args.lesson_command == "add":
            result = service.capture_life_lesson(lesson_text=args.text, privacy_scope=args.privacy_scope, raw_text=args.raw_text)
            payload = {"capture_id": result.capture_id, "life_lesson_id": result.record_id}
        elif args.lesson_command == "list":
            payload = store.list_life_lessons(args.query, args.limit)
        else:
            payload = store.get_life_lesson(args.lesson_id)
        print(json_output(payload))
        return 0
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
            print(json_output(payload))
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
            print(json_output(payload))
        else:
            print(f"{task['title']} ({task['status']})")
            print(task["description"])
            for event in events:
                print(f"- {event['occurred_at']} {event['event_type']}: {event['message']}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
