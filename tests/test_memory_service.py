from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.memory.service import MemoryService
from app.storage.database import Base


def test_memory_service_stores_and_retrieves_memory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        service = MemoryService(db)

        service.store_memory(
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is PAYMENTS",
            source="jira",
            confidence=0.95,
            importance=0.9,
        )

        memories = service.get_memories("payments")

        assert len(memories) == 1

        memory = memories[0]

        assert memory.content == "Production Jira project is PAYMENTS"
        assert memory.memory_type == "FACT"
        assert memory.source == "jira"
        assert memory.confidence == 0.95
        assert memory.importance == 0.9


def test_memory_service_can_invalidate_memory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        service = MemoryService(db)

        memory = service.store_memory(
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is PAYMENTS",
            source="jira",
        )

        assert memory.valid_until is None

        service.invalidate_memory(memory)

        memories = service.get_memories("payments")

        assert len(memories) == 0


def test_memory_persists_across_database_sessions(tmp_path: Path):
    database_path = tmp_path / "memory.db"
    database_url = f"sqlite:///{database_path}"

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    # First workflow execution
    with SessionLocal() as db:
        service = MemoryService(db)

        service.store_memory(
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is PAYMENTS",
            source="jira",
            confidence=0.95,
            importance=0.9,
        )

    # First execution has finished.
    # Create a completely new database session.
    with SessionLocal() as db:
        service = MemoryService(db)

        memories = service.get_memories("payments")

        assert len(memories) == 1
        assert memories[0].content == "Production Jira project is PAYMENTS"


def test_memory_service_excludes_invalidated_memories():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        service = MemoryService(db)

        old_memory = service.store_memory(
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is PAYMENTS",
            source="jira",
        )

        service.invalidate_memory(old_memory)

        service.store_memory(
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is CHECKOUT",
            source="jira",
        )

        memories = service.get_memories("payments")

        assert len(memories) == 1
        assert memories[0].content == "Production Jira project is CHECKOUT"

def test_memory_service_can_update_memory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        service = MemoryService(db)

        old_memory = service.store_memory(
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is PAYMENTS",
            source="jira",
        )

        new_memory = service.update_memory(
            memory=old_memory,
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is CHECKOUT",
            source="jira",
        )

        memories = service.get_memories("payments")

        assert len(memories) == 1
        assert memories[0].content == "Production Jira project is CHECKOUT"
        assert memories[0].id == new_memory.id
        assert old_memory.valid_until is not None