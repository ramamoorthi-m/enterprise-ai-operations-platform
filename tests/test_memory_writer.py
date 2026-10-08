from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.memory.models import Memory
from app.storage.database import Base
from app.workflow.memory_writer import memory_writer


def test_memory_writer_stores_key_findings():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        state = {
            "project": "SCRUM",
            "confidence": 0.9,
            "analysis": {
                "key_findings": [
                    "GitHub deployment failed during database migration.",
                    "Three Jira tasks remain blocked.",
                ],
            },
        }

        with patch(
            "app.workflow.memory_writer.SessionLocal",
            return_value=db,
        ):
            result = memory_writer(state)

        memories = (
            db.query(Memory)
            .filter(
                Memory.project_id == "SCRUM",
                Memory.valid_until.is_(None),
            )
            .all()
        )

        assert result["memory_write_status"] == "written"
        assert result["memory_write_count"] == 2
        assert len(memories) == 2

        contents = {memory.content for memory in memories}

        assert (
            "GitHub deployment failed during database migration."
            in contents
        )
        assert (
            "Three Jira tasks remain blocked."
            in contents
        )

        assert all(
            memory.memory_type == "FACT"
            for memory in memories
        )


def test_memory_writer_skips_low_confidence_analysis():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        state = {
            "project": "SCRUM",
            "confidence": 0.4,
            "analysis": {
                "key_findings": [
                    "This finding is uncertain."
                ],
            },
        }

        with patch(
            "app.workflow.memory_writer.SessionLocal",
            return_value=db,
        ):
            result = memory_writer(state)

        memories = db.query(Memory).all()

        assert result["memory_write_status"] == "skipped"
        assert len(memories) == 0


def test_memory_writer_skips_when_no_findings_exist():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        state = {
            "project": "SCRUM",
            "confidence": 0.9,
            "analysis": {
                "key_findings": [],
            },
        }

        with patch(
            "app.workflow.memory_writer.SessionLocal",
            return_value=db,
        ):
            result = memory_writer(state)

        assert result["memory_write_status"] == "skipped"
        assert db.query(Memory).count() == 0


def test_memory_writer_does_not_duplicate_existing_finding():
    engine = create_engine("sqlite:///:memory:")