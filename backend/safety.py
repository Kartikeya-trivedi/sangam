"""Child safety + responsible data (spec §12). These are rubric points — keep intact.

- Minors are NEVER broadcast publicly. /announce is blocked when is_minor; instead a
  private staff alert + guardian-verification task is created.
- Audit log on every match-confirm, announcement, and record access.
- Data minimization & no PII (phone/name) in logs or URLs (§12.7).

Scaffold uses in-memory stores; back these with the audit_log table + a staff-alert
table/queue in production.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from models import Person

_audit: list[dict] = []
_staff_alerts: list[dict] = []


def is_minor(person: Person) -> bool:
    return person.is_minor or person.age_band in ("child", "teen")


def audit(actor: str, action: str, person_id: str | None = None, **meta) -> None:
    """Append to the audit log. NEVER put phone numbers or names in meta (§12.7)."""
    _audit.append(
        {
            "id": str(uuid.uuid4()),
            "actor": actor,
            "action": action,
            "person_id": person_id,
            "meta": meta,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )


def create_staff_alert(person: Person, centre_id: str | None = None) -> dict:
    """Private alert for a minor/vulnerable match — opens guardian verification (§12.1, §12.2)."""
    alert = {
        "id": str(uuid.uuid4()),
        "person_id": person.id,
        "centre_id": centre_id or person.centre_id,
        "type": "minor_match" if is_minor(person) else "vulnerable_match",
        "guardian_verified": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _staff_alerts.append(alert)
    audit("system", "staff_alert_created", person.id, type=alert["type"])
    return alert


def redact_person(person: Person) -> dict:
    """Public-safe view: no phone, no embedding; minors lose photo_ref too (§12.3)."""
    data = person.model_dump()
    data.pop("contact_phone", None)
    data.pop("face_embedding", None)
    if is_minor(person):
        data.pop("photo_ref", None)
    return data


def audit_log() -> list[dict]:
    return list(_audit)


def staff_alerts() -> list[dict]:
    return list(_staff_alerts)
