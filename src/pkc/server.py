from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .app import CaptureService, KnowledgeStore


class CoordinatorHandler(BaseHTTPRequestHandler):
    server_version = "PKCCoordinator/0.1"

    @property
    def store(self) -> KnowledgeStore:
        return self.server.store  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._json({"ok": True})
            return
        if path == "/inbox":
            self.store.initialize()
            self._json(self.store.inbox())
            return
        query = parse_qs(urlparse(self.path).query)
        if path in {"/quotes", "/life-lessons"}:
            try:
                limit = int(query.get("limit", ["20"])[0])
                if not 1 <= limit <= 100:
                    raise ValueError
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "limit must be 1..100")
                return
            self.store.initialize()
            records = self.store.list_quotes(query.get("query", [""])[0], limit) if path == "/quotes" else self.store.list_life_lessons(query.get("query", [""])[0], limit)
            self._json(records)
            return
        for prefix, getter in (("/quotes/", self.store.get_quote), ("/life-lessons/", self.store.get_life_lesson)):
            if path.startswith(prefix):
                self.store.initialize()
                record = getter(path.removeprefix(prefix))
                if record is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "not found")
                else:
                    self._json(record)
                return
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in {"/capture", "/quotes", "/life-lessons"}:
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            self.send_error(HTTPStatus.BAD_REQUEST, "expected JSON object")
            return

        self.store.initialize()
        service = CaptureService(self.store)
        try:
            if path == "/quotes":
                result = service.capture_quote(
                    exact_text=payload["exact_text"], speaker=payload.get("speaker"), source_label=payload.get("source_label"), source_locator=payload.get("source_locator"), attribution_confidence=payload.get("attribution_confidence", 50), attribution_status=payload.get("attribution_status", "unknown"), privacy_scope=payload.get("privacy_scope", "personal"), raw_text=payload.get("raw_text"),
                )
                self._json({"capture_id": result.capture_id, "quote_id": result.record_id}, status=HTTPStatus.CREATED)
                return
            if path == "/life-lessons":
                result = service.capture_life_lesson(lesson_text=payload["lesson_text"], privacy_scope=payload.get("privacy_scope", "personal"), raw_text=payload.get("raw_text"))
                self._json({"capture_id": result.capture_id, "life_lesson_id": result.record_id}, status=HTTPStatus.CREATED)
                return
            result = service.capture(payload["text"])
        except (KeyError, TypeError, ValueError):
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid capture payload")
            return
        self._json(
            {
                "capture_id": result.capture_id,
                "task_ids": result.task_ids,
                "observation_ids": result.observation_ids,
                "conversation_ids": result.conversation_ids,
                "commitment_ids": result.commitment_ids,
            },
            status=HTTPStatus.CREATED,
        )

    def log_message(self, format: str, *args: object) -> None:
        # Keep systemd logs quiet and avoid writing request bodies/secrets.
        return

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class CoordinatorServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], store: KnowledgeStore):
        super().__init__(server_address, CoordinatorHandler)
        self.store = store


def main() -> int:
    host = os.environ.get("PKC_HOST", "127.0.0.1")
    port = int(os.environ.get("PKC_PORT", "8765"))
    store = KnowledgeStore.from_env()
    store.initialize()
    server = CoordinatorServer((host, port), store)
    print(f"pkc-api listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
