from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

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
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/capture":
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
            text = payload["text"]
        except (json.JSONDecodeError, KeyError, TypeError):
            self.send_error(HTTPStatus.BAD_REQUEST, "expected JSON body with text")
            return

        self.store.initialize()
        result = CaptureService(self.store).capture(text)
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
