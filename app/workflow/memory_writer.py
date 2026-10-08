from app.memory.service import MemoryService
from app.storage.database import SessionLocal
from app.state.state import EnterpriseState


MIN_MEMORY_CONFIDENCE = 0.6
DEFAULT_MEMORY_IMPORTANCE = 0.8


def memory_writer(state: EnterpriseState):
    """Persist durable findings from a completed investigation."""

    # Do not write memory if the final report failed output validation.
    if state.get("status") == "output_guardrail_failed":
        return {
            "memory_write_status": "skipped",
        }

    project_id = state.get("project")
    analysis = state.get("analysis", {})
    confidence = state.get("confidence", 0.0)

    if not project_id:
        return {
            "memory_write_status": "skipped",
        }

    if confidence < MIN_MEMORY_CONFIDENCE:
        return {
            "memory_write_status": "skipped",
        }

    key_findings = analysis.get("key_findings", [])

    if not key_findings:
        return {
            "memory_write_status": "skipped",
        }

    db = SessionLocal()

    try:
        service = MemoryService(db)

        stored_count = 0

        for finding in key_findings:
            if not finding:
                continue

            service.store_if_new(
                project_id=project_id,
                memory_type="FACT",
                content=finding,
                source="workflow_analysis",
                confidence=confidence,
                importance=DEFAULT_MEMORY_IMPORTANCE,
            )

            stored_count += 1

        return {
            "memory_write_status": "written",
            "memory_write_count": stored_count,
        }

    finally:
        db.close()