import uuid
from typing import Optional
import asyncpg


async def write_audit(
    conn:             asyncpg.Connection,
    event_type:       str,
    actor:            Optional[dict]      = None,
    visit_request_id: Optional[uuid.UUID] = None,
    visitor_id:       Optional[uuid.UUID] = None,
    visitor_name:     Optional[str]       = None,
    detail:           Optional[str]       = None,
):
    await conn.execute(
        """
        INSERT INTO audit_log
          (event_type, actor_staff_id, actor_name, visit_request_id, visitor_id, visitor_name, detail)
        VALUES ($1,$2,$3,$4,$5,$6,$7)
        """,
        event_type,
        uuid.UUID(str(actor["id"])) if actor else None,
        actor["name"] if actor else None,
        visit_request_id,
        visitor_id,
        visitor_name,
        detail,
    )
