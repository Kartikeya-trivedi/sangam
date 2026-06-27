"""Child-safety, consent, audit, and data-retention (TTL) enforcement.

Child safety is non-negotiable: a minor is NEVER publicly announced; a match involving a minor
requires guardian verification before confirmation; every confirm/announce/access is audited; no
PII (name/phone) is written to logs. Records auto-purge after TTL_DAYS (face embeddings + photos
are cleared first).
"""
from __future__ import annotations

from datetime import datetime, timezone

from db import repo
from models import Person

# convenience re-export so routers can `from safety import audit`
audit = repo.write_audit


def is_minor(person: Person) -> bool:
    return bool(person.is_minor)


def match_requires_guardian(lost: Person, found: Person) -> bool:
    return bool(lost.is_minor or found.is_minor)


def can_announce(person: Person) -> tuple[bool, str]:
    """(allowed, reason). Minors are never publicly announced (privacy + anti-trafficking)."""
    if person.is_minor:
        return False, "minor_announcement_blocked"
    return True, ""


def purge_expired() -> int:
    """Clear sensitive fields + mark 'expired' for records past TTL. Returns count purged.

    Keeps the row shell (status='expired') for the audit trail; wipes face_embedding + photo.
    """
    conn = repo.get_conn()
    now = datetime.now(timezone.utc).isoformat()
    rows = conn.execute(
        "SELECT id FROM persons WHERE ttl_expires_at < ? AND status != 'expired'", (now,)
    ).fetchall()
    for r in rows:
        conn.execute(
            "UPDATE persons SET face_embedding=NULL, photo_storage_key=NULL, status='expired',"
            " updated_at=? WHERE id=?",
            (now, r["id"]),
        )
        repo.write_audit("system", "record_expired", person_id=r["id"])
    conn.commit()
    return len(rows)
