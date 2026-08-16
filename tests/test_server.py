from __future__ import annotations

import json
from http.client import HTTPConnection
from threading import Thread

from pkc.app import KnowledgeStore
from pkc.server import CoordinatorServer


def test_capture_http_api_round_trip(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.initialize()
    server = CoordinatorServer(("127.0.0.1", 0), store)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request(
            "POST",
            "/capture",
            body=json.dumps({"text": "I don't like the UI for the Parts Advisor page in part-suite."}),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 201
        assert payload["task_ids"]

        conn.request("GET", "/inbox")
        inbox_response = conn.getresponse()
        inbox = json.loads(inbox_response.read().decode("utf-8"))
        assert inbox_response.status == 200
        assert inbox[0]["project_slug"] == "part-suite"
        assert inbox[0]["assigned_agent"] == "developer"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
