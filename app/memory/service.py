from datetime import datetime

from sqlalchemy.orm import Session

from app.memory.models import Memory
from app.memory.repository import MemoryRepository


class MemoryService:

    def __init__(self, db: Session):
        self.repository = MemoryRepository(db)

    def store_memory(
        self,
        project_id: str,
        memory_type: str,
        content: str,
        source: str,
        confidence: float = 1.0,
        importance: float = 0.5,
        valid_until: datetime | None = None,
    ) -> Memory:
        memory = Memory(
            project_id=project_id,
            memory_type=memory_type,
            content=content,
            source=source,
            confidence=confidence,
            importance=importance,
            valid_until=valid_until,
        )

        return self.repository.create(memory)

    def store_if_new(
        self,
        project_id: str,
        memory_type: str,
        content: str,
        source: str,
        confidence: float = 1.0,
        importance: float = 0.5,
        valid_until: datetime | None = None,
    ) -> Memory:
        existing = self.repository.get_active_by_content(
            project_id=project_id,
            content=content,
        )

        if existing:
            return existing

        return self.store_memory(
            project_id=project_id,
            memory_type=memory_type,
            content=content,
            source=source,
            confidence=confidence,
            importance=importance,
            valid_until=valid_until,
        )

    def get_memories(
        self,
        project_id: str,
    ) -> list[Memory]:
        return self.repository.get_by_project(project_id)

    def invalidate_memory(
        self,
        memory: Memory,
    ) -> Memory:
        return self.repository.invalidate(memory)

    def update_memory(
        self,
        memory: Memory,
        project_id: str,
        memory_type: str,
        content: str,
        source: str,
        confidence: float = 1.0,
        importance: float = 0.5,
        valid_until: datetime | None = None,
    ) -> Memory:
        self.invalidate_memory(memory)

        return self.store_memory(
            project_id=project_id,
            memory_type=memory_type,
            content=content,
            source=source,
            confidence=confidence,
            importance=importance,
            valid_until=valid_until,
        )