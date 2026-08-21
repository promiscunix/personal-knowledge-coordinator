from datetime import UTC, datetime

from pkc.cli import json_output


def test_json_output_serializes_postgresql_datetime_values():
    rendered = json_output({"created_at": datetime(2026, 8, 21, tzinfo=UTC)})

    assert '"created_at": "2026-08-21 00:00:00+00:00"' in rendered
