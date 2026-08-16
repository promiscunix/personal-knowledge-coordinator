from pkc.app import CaptureService, KnowledgeStore


def test_parts_advisor_capture_preserves_raw_and_creates_project_task(tmp_path):
    db_path = tmp_path / "knowledge.sqlite3"
    store = KnowledgeStore(db_path)
    store.initialize()
    service = CaptureService(store, agent_name="coordinator")

    result = service.capture("I don't like the UI for the Parts Advisor page in part-suite.")

    capture = store.get_raw_capture(result.capture_id)
    assert capture["raw_text"] == "I don't like the UI for the Parts Advisor page in part-suite."
    assert capture["source_type"] == "direct_input"
    assert capture["privacy_scope"] == "project:part-suite"

    task = store.get_task(result.task_ids[0])
    assert task["title"] == "Inspect Parts Advisor UI concerns"
    assert task["status"] == "captured"
    assert task["project_slug"] == "part-suite"
    assert task["source_capture_id"] == result.capture_id
    assert task["assigned_agent"] == "developer"

    observation = store.get_observation(result.observation_ids[0])
    assert observation["summary"] == "User reported Parts Advisor UI concerns in part-suite."
    assert observation["verified"] == 0
    assert observation["source_capture_id"] == result.capture_id

    events = store.activity_for("task", result.task_ids[0])
    assert [event["event_type"] for event in events] == ["created", "assigned"]


def test_management_conversation_is_private_and_extracts_commitment(tmp_path):
    db_path = tmp_path / "knowledge.sqlite3"
    store = KnowledgeStore(db_path)
    store.initialize()
    service = CaptureService(store, agent_name="coordinator")

    result = service.capture(
        "Talked to Tom about missing callbacks again. He says he gets distracted when the counter gets busy. "
        "We agreed he'll check the list at 11 and 3."
    )

    capture = store.get_raw_capture(result.capture_id)
    assert capture["privacy_scope"] == "management-private"

    person = store.get_person_by_name("Tom")
    assert person is not None

    conversation = store.get_conversation(result.conversation_ids[0])
    assert conversation["person_id"] == person["id"]
    assert conversation["issue"] == "missing callbacks"
    assert conversation["attributed_explanation"] == "Tom says he gets distracted when the counter gets busy."
    assert conversation["privacy_scope"] == "management-private"

    commitment = store.get_commitment(result.commitment_ids[0])
    assert commitment["person_id"] == person["id"]
    assert commitment["summary"] == "Tom will check the callback list at 11 and 3."
    assert commitment["source_capture_id"] == result.capture_id
    assert commitment["privacy_scope"] == "management-private"


def test_inbox_returns_open_tasks_with_source_and_project(tmp_path):
    db_path = tmp_path / "knowledge.sqlite3"
    store = KnowledgeStore(db_path)
    store.initialize()
    service = CaptureService(store, agent_name="coordinator")
    service.capture("I don't like the UI for the Parts Advisor page in part-suite.")

    inbox = store.inbox()

    assert len(inbox) == 1
    assert inbox[0]["title"] == "Inspect Parts Advisor UI concerns"
    assert inbox[0]["project_slug"] == "part-suite"
    assert "Parts Advisor" in inbox[0]["raw_text"]
