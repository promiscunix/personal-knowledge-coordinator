import json

from pkc.cli import main


def test_quote_cli_add_then_list(tmp_path, capsys):
    database = tmp_path / "knowledge.sqlite3"
    assert main(["--db", str(database), "quote", "add", "--text", "Practice makes reliable.", "--json"]) == 0
    added = json.loads(capsys.readouterr().out)
    assert added["quote_id"]
    assert main(["--db", str(database), "quote", "list", "--query", "reliable", "--json"]) == 0
    records = json.loads(capsys.readouterr().out)
    assert records[0]["id"] == added["quote_id"]
