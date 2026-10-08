from app.memory.service import MemoryService
from app.storage.database import SessionLocal
from app.state.state import EnterpriseState


def memory_retrieval(state: EnterpriseState):
    """Retrieve active persistent business memories for the current project."""

    project_id = state.get("project")

    if not project_id:
        return {
            "memory_context": [],
        }

    db = SessionLocal()

    try:
        service = MemoryService(db)

        memories = service.get_memories(project_id)

        memory_context = [
            {
                "memory_type": memory.memory_type,
                "content": memory.content,
                "source": memory.source,
                "confidence": memory.confidence,
                "importance": memory.importance,
            }
            for memory in memories
        ]

        return {
            "memory_context": memory_context,
        }

    finally:
        db.close()