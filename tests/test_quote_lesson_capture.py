from pkc.app import CaptureService, KnowledgeStore


def test_quote_capture_preserves_raw_provenance_and_attribution(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.initialize()
    service = CaptureService(store, agent_name="coordinator")

    result = service.capture_quote(
        exact_text="Momentum comes from movement, not motivation.",
        speaker="Unknown / video speaker",
        source_label="SELF learning video",
        source_locator="https://example.test/video#t=808",
        attribution_confidence=60,
        attribution_status="likely",
        raw_text="This is a great quote; save it.",
    )

    quote = store.get_quote(result.record_id)
    capture = store.get_raw_capture(result.capture_id)
    assert quote["exact_text"] == "Momentum comes from movement, not motivation."
    assert quote["speaker"] == "Unknown / video speaker"
    assert quote["attribution_confidence"] == 60
    assert quote["attribution_status"] == "likely"
    assert quote["source_capture_id"] == result.capture_id
    assert capture["raw_text"] == "This is a great quote; save it."
    assert capture["source_type"] == "quote"


def test_life_lesson_capture_preserves_raw_provenance(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.initialize()
    service = CaptureService(store, agent_name="coordinator")

    result = service.capture_life_lesson(
        lesson_text="Useful learning should lead to action.",
        raw_text="Keep this lesson.",
    )

    lesson = store.get_life_lesson(result.record_id)
    capture = store.get_raw_capture(result.capture_id)
    assert lesson["lesson_text"] == "Useful learning should lead to action."
    assert lesson["source_capture_id"] == result.capture_id
    assert capture["raw_text"] == "Keep this lesson."
    assert capture["source_type"] == "life_lesson"
