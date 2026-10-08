from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.memory.models import Memory
from app.storage.database import Base
from app.workflow.memory import memory_retrieval
from app.workflow.memory_writer import memory_writer
from app.workflow.planner import planner
from app.llm.client import GeminiClient


def test_memory_retrieval_loads_persistent_business_memory(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        memory = Memory(
            project_id="SCRUM",
            memory_type="FACT",
            content="Production Jira project is SCRUM",
            source="jira",
            confidence=0.95,
            importance=0.9,
        )

        db.add(memory)
        db.commit()

        monkeypatch.setattr(
            "app.workflow.memory.SessionLocal",
            lambda: db,
        )

        result = memory_retrieval(
            {
                "project": "SCRUM",
            }
        )

        assert len(result["memory_context"]) == 1

        retrieved_memory = result["memory_context"][0]

        assert (
            retrieved_memory["content"]
            == "Production Jira project is SCRUM"
        )
        assert retrieved_memory["memory_type"] == "FACT"
        assert retrieved_memory["source"] == "jira"
        assert retrieved_memory["confidence"] == 0.95
        assert retrieved_memory["importance"] == 0.9


def test_memory_survives_workflow_run_and_reaches_planner(
    monkeypatch,
    tmp_path,
):
    # ---------------------------------------------------------
    # Create a file-based SQLite database.
    #
    # A file-based database is intentional here because we want
    # to simulate two separate workflow executions.
    # ---------------------------------------------------------

    database_path = tmp_path / "memory.db"

    engine = create_engine(
        f"sqlite:///{database_path}",
    )

    Base.metadata.create_all(engine)

    TestSessionLocal = sessionmaker(bind=engine)

    # ---------------------------------------------------------
    # Use the temporary database for both writer and retrieval.
    # ---------------------------------------------------------

    monkeypatch.setattr(
        "app.workflow.memory_writer.SessionLocal",
        TestSessionLocal,
    )

    monkeypatch.setattr(
        "app.workflow.memory.SessionLocal",
        TestSessionLocal,
    )

    # =========================================================
    # WORKFLOW A
    # =========================================================
    #
    # The first workflow discovers durable business knowledge.
    #
    # =========================================================

    writer_state = {
        "project": "SCRUM",
        "confidence": 0.9,
        "analysis": {
            "key_findings": [
                "GitHub deployment failed during database migration.",
            ],
        },
        "status": "report_generated",
    }

    write_result = memory_writer(writer_state)

    assert write_result["memory_write_status"] == "written"
    assert write_result["memory_write_count"] == 1

    # ---------------------------------------------------------
    # Verify that the memory was actually persisted.
    # ---------------------------------------------------------

    with TestSessionLocal() as db:
        memories = (
            db.query(Memory)
            .filter(
                Memory.project_id == "SCRUM",
                Memory.valid_until.is_(None),
            )
            .all()
        )

        assert len(memories) == 1

        assert (
            memories[0].content
            == "GitHub deployment failed during database migration."
        )

        assert memories[0].memory_type == "FACT"
        assert memories[0].source == "workflow_analysis"

    # =========================================================
    # WORKFLOW B
    # =========================================================
    #
    # A new workflow execution retrieves the memory.
    #
    # =========================================================

    retrieval_result = memory_retrieval(
        {
            "project": "SCRUM",
        }
    )

    memory_context = retrieval_result["memory_context"]

    assert len(memory_context) == 1

    assert (
        memory_context[0]["content"]
        == "GitHub deployment failed during database migration."
    )

    assert memory_context[0]["memory_type"] == "FACT"
    assert memory_context[0]["source"] == "workflow_analysis"
    assert memory_context[0]["confidence"] == 0.9
    assert memory_context[0]["importance"] == 0.8

    # =========================================================
    # PLANNER
    # =========================================================
    #
    # The planner must receive the persistent memory.
    #
    # IMPORTANT:
    # Gemini is mocked. This test does NOT consume Gemini API
    # quota.
    #
    # =========================================================

    captured_prompt = {}

    def fake_generate_structured(
        self,
        prompt,
        response_schema,
    ):
        captured_prompt["value"] = prompt

        return response_schema(
            project="SCRUM",
            goal="Investigate current project status.",
            tasks=[],
            required_sources=[],
        )

    # Patch the GeminiClient method itself.
    #
    # This is safe because the planner uses GeminiClient for
    # structured generation.
    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    planner_result = planner(
        {
            "user_query": (
                "What should we investigate about the current "
                "project status?"
            ),
            "project": "SCRUM",
            "memory_context": memory_context,
            "retry_count": 0,
        }
    )

    # ---------------------------------------------------------
    # Verify that the persistent memory reached the planner
    # prompt.
    # ---------------------------------------------------------

    prompt = captured_prompt["value"]

    assert (
        "GitHub deployment failed during database migration."
        in prompt
    )

    assert "[FACT]" in prompt
    assert "workflow_analysis" in prompt

    # ---------------------------------------------------------
    # Verify planner still returned a valid plan.
    # ---------------------------------------------------------

    assert planner_result["plan"] is not None