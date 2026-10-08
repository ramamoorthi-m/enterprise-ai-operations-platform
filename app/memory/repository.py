from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.memory.models import Memory


class MemoryRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, memory: Memory) -> Memory:
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def get_by_project(
        self,
        project_id: str,
    ) -> list[Memory]:
        statement = (
            select(Memory)
            .where(
                Memory.project_id == project_id,
                Memory.valid_until.is_(None),
            )
            .order_by(Memory.updated_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def get_active_by_content(
        self,
        project_id: str,
        content: str,
    ) -> Memory | None:
        statement = (
            select(Memory)
            .where(
                Memory.project_id == project_id,
                Memory.content == content,
                Memory.valid_until.is_(None),
            )
        )

        return self.db.scalars(statement).first()

    def invalidate(self, memory: Memory) -> Memory:
        memory.valid_until = datetime.utcnow()

        self.db.commit()
        self.db.refresh(memory)

        return memory