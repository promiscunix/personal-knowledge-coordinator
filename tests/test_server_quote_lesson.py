import json
from datetime import UTC, datetime
from http.client import HTTPConnection
from threading import Thread

from pkc.app import KnowledgeStore
from pkc.server import CoordinatorServer


def test_quote_api_post_then_get(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.initialize()
    server = CoordinatorServer(("127.0.0.1", 0), store)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("POST", "/quotes", body=json.dumps({"exact_text": "Keep it simple."}), headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        created = json.loads(response.read().decode())
        assert response.status == 201
        conn.request("GET", f"/quotes/{created['quote_id']}")
        response = conn.getresponse()
        quote = json.loads(response.read().decode())
        assert response.status == 200
        assert quote["exact_text"] == "Keep it simple."
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_quote_list_api_serializes_postgresql_datetime_values():
    class PostgresLikeStore:
        def initialize(self):
            pass

        def list_quotes(self, query, limit):
            return [{"id": "quote-1", "created_at": datetime(2026, 8, 22, tzinfo=UTC)}]

    server = CoordinatorServer(("127.0.0.1", 0), PostgresLikeStore())
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/quotes?query=smoke")
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        assert response.status == 200
        assert payload[0]["created_at"] == "2026-08-22 00:00:00+00:00"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
