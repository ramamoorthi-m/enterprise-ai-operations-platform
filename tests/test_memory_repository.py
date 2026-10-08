from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.memory.models import Memory
from app.memory.repository import MemoryRepository
from app.storage.database import Base


def test_memory_can_be_created_and_retrieved():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        repository = MemoryRepository(db)

        memory = Memory(
            project_id="payments",
            memory_type="FACT",
            content="Production Jira project is PAYMENTS",
            source="jira",
            confidence=0.95,
            importance=0.9,
        )

        repository.create(memory)

        memories = repository.get_by_project("payments")

        assert len(memories) == 1
        assert memories[0].content == "Production Jira project is PAYMENTS"
        assert memories[0].memory_type == "FACT"