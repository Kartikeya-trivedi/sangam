"""Repository: typed CRUD over the SQLite store. All Person <-> row mapping lives here."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from config import settings
from constants import AGE_BAND_INDEX, AGE_BANDS
from db.connection import get_conn
from models import Person

_LIST_FIELDS = ("clothing", "distinguishing_features", "languages_spoken")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- serialization -------------------------------------------------------------------------
def person_to_row(p: Person) -> dict[str, Any]:
    d = p.model_dump()
    row: dict[str, Any] = {}
    for k, v in d.items():
        if k in _LIST_FIELDS:
            row[k] = json.dumps(v or [])
        elif k == "face_embedding":
            row[k] = json.dumps(v) if v else None
        elif k in ("is_minor", "consent_given"):
            row[k] = 1 if v else 0
        elif isinstance(v, datetime):
            row[k] = v.isoformat()
        else:
            row[k] = v
    return row


def row_to_person(row: sqlite3.Row) -> Person:
    d = dict(row)
    for f in _LIST_FIELDS:
        d[f] = json.loads(d.get(f) or "[]")
    fe = d.get("face_embedding")
    d["face_embedding"] = json.loads(fe) if fe else None
    d["is_minor"] = bool(d.get("is_minor"))
    d["consent_given"] = bool(d.get("consent_given"))
    # Pydantic coerces ISO strings -> datetime for the datetime-typed fields.
    return Person.model_validate({k: d.get(k) for k in Person.model_fields})


# --- writes --------------------------------------------------------------------------------
_INSERT_COLS = [
    "id", "role", "age_band", "gender", "name", "clothing", "distinguishing_features",
    "height_band", "languages_spoken", "last_seen_location", "last_seen_time",
    "reporter_name", "reporter_mobile", "spoken_language", "raw_transcript", "native_summary",
    "face_embedding", "photo_storage_key", "photo_location_hint", "is_minor", "consent_given",
    "centre_id", "centre_zone", "status", "created_at", "ttl_expires_at", "updated_at",
]


def insert_person(p: Person, *, test_pair_id: str | None = None,
                  test_should_match: int | None = None) -> Person:
    conn = get_conn()
    if p.created_at is None:
        p.created_at = datetime.now(timezone.utc)
    if p.ttl_expires_at is None:
        p.ttl_expires_at = p.created_at + timedelta(days=settings.ttl_days)
    p.updated_at = datetime.now(timezone.utc)
    row = person_to_row(p)
    cols = _INSERT_COLS + ["test_pair_id", "test_should_match"]
    vals = [row.get(c) for c in _INSERT_COLS] + [test_pair_id, test_should_match]
    placeholders = ",".join("?" for _ in cols)
    conn.execute(f"INSERT INTO persons ({','.join(cols)}) VALUES ({placeholders})", vals)
    conn.execute(
        "INSERT INTO persons_fts (person_id, name, raw_transcript) VALUES (?,?,?)",
        (p.id, p.name or "", p.raw_transcript or ""),
    )
    conn.commit()
    return p


def insert_many(persons: list[Person], *, test_pair_id_fn=None) -> int:
    """Bulk insert in a single transaction (fast seeding). Sets created_at/ttl defaults per row."""
    conn = get_conn()
    cols = _INSERT_COLS + ["test_pair_id", "test_should_match"]
    placeholders = ",".join("?" for _ in cols)
    person_rows, fts_rows = [], []
    for p in persons:
        if p.created_at is None:
            p.created_at = datetime.now(timezone.utc)
        if p.ttl_expires_at is None:
            p.ttl_expires_at = p.created_at + timedelta(days=settings.ttl_days)
        p.updated_at = datetime.now(timezone.utc)
        row = person_to_row(p)
        tp, tsm = (test_pair_id_fn(p) if test_pair_id_fn else (None, None))
        person_rows.append([row.get(c) for c in _INSERT_COLS] + [tp, tsm])
        fts_rows.append((p.id, p.name or "", p.raw_transcript or ""))
    conn.executemany(f"INSERT INTO persons ({','.join(cols)}) VALUES ({placeholders})", person_rows)
    conn.executemany(
        "INSERT INTO persons_fts (person_id, name, raw_transcript) VALUES (?,?,?)", fts_rows)
    conn.commit()
    return len(persons)


def get_person(person_id: str) -> Optional[Person]:
    row = get_conn().execute("SELECT * FROM persons WHERE id=?", (person_id,)).fetchone()
    return row_to_person(row) if row else None


def update_status(person_id: str, status: str) -> None:
    get_conn().execute(
        "UPDATE persons SET status=?, updated_at=? WHERE id=?",
        (status, _now_iso(), person_id),
    )
    get_conn().commit()


# --- candidate retrieval (matching engine Stage 1: fast SQL filter) ------------------------
def adjacent_age_bands(age_band: str, span: int = 1) -> list[str]:
    """The band plus +/-span neighbours; empty (=> no age filter) when unknown."""
    if age_band not in AGE_BAND_INDEX:
        return []
    i = AGE_BAND_INDEX[age_band]
    lo, hi = max(0, i - span), min(len(AGE_BANDS) - 1, i + span)
    return list(AGE_BANDS[lo : hi + 1])


def candidates_for(query: Person, limit: int = 300, *, only_open: bool = True) -> list[Person]:
    """Opposite-role records, gender-compatible, within +/-1 age band. Pre-filter before scoring."""
    opposite = "found" if query.role == "lost" else "lost"
    sql = ["SELECT * FROM persons WHERE role=? AND id<>?"]
    args: list[Any] = [opposite, query.id]
    if only_open:
        sql.append("AND status='open'")
    # Gender is a hard constraint downstream; pre-filter unless the query gender is unknown.
    if query.gender in ("male", "female"):
        sql.append("AND gender IN (?, 'unknown')")
        args.append(query.gender)
    bands = adjacent_age_bands(query.age_band)
    if bands:
        sql.append(f"AND (age_band IN ({','.join('?' for _ in bands)}) OR age_band='unknown')")
        args.extend(bands)
    sql.append("ORDER BY created_at DESC LIMIT ?")
    args.append(limit)
    rows = get_conn().execute(" ".join(sql), args).fetchall()
    return [row_to_person(r) for r in rows]


def open_persons(role: str, limit: int = 1000) -> list[Person]:
    rows = get_conn().execute(
        "SELECT * FROM persons WHERE role=? AND status='open' ORDER BY created_at DESC LIMIT ?",
        (role, limit),
    ).fetchall()
    return [row_to_person(r) for r in rows]


def fts_search(query: str, limit: int = 50) -> list[str]:
    """Return person_ids matching a free-text query (name/transcript). Best-effort."""
    if not query.strip():
        return []
    try:
        rows = get_conn().execute(
            "SELECT person_id FROM persons_fts WHERE persons_fts MATCH ? LIMIT ?",
            (query, limit),
        ).fetchall()
        return [r["person_id"] for r in rows]
    except sqlite3.OperationalError:
        return []


def persons_by_test_pair(pair_id: str) -> list[Person]:
    rows = get_conn().execute(
        "SELECT * FROM persons WHERE test_pair_id=? ORDER BY role", (pair_id,)
    ).fetchall()
    return [row_to_person(r) for r in rows]


def test_pairs() -> list[tuple[str, int]]:
    """Distinct (test_pair_id, test_should_match) for the evaluation harness."""
    rows = get_conn().execute(
        "SELECT DISTINCT test_pair_id, test_should_match FROM persons "
        "WHERE test_pair_id IS NOT NULL ORDER BY test_pair_id"
    ).fetchall()
    return [(r["test_pair_id"], r["test_should_match"]) for r in rows]


def clear_test_pairs() -> int:
    conn = get_conn()
    ids = [r["id"] for r in conn.execute(
        "SELECT id FROM persons WHERE test_pair_id IS NOT NULL").fetchall()]
    conn.execute("DELETE FROM persons WHERE test_pair_id IS NOT NULL")
    conn.executemany("DELETE FROM persons_fts WHERE person_id=?", [(i,) for i in ids])
    conn.commit()
    return len(ids)


# --- listing / pagination (ops dashboard) --------------------------------------------------
_SORTABLE = {"created_at", "age_band", "status", "updated_at"}


def list_persons(*, status: str | None = None, role: str | None = None,
                 centre_id: str | None = None, is_minor: bool | None = None,
                 page: int = 1, per_page: int = 50, sort_by: str = "created_at",
                 sort_order: str = "desc") -> tuple[list[Person], int]:
    where: list[str] = ["1=1"]
    args: list[Any] = []
    if status:
        where.append("status=?")
        args.append(status)
    if role:
        where.append("role=?")
        args.append(role)
    if centre_id:
        where.append("centre_id=?")
        args.append(centre_id)
    if is_minor is not None:
        where.append("is_minor=?")
        args.append(1 if is_minor else 0)
    clause = " AND ".join(where)
    total = get_conn().execute(f"SELECT COUNT(*) c FROM persons WHERE {clause}", args).fetchone()["c"]
    sort_by = sort_by if sort_by in _SORTABLE else "created_at"
    order = "DESC" if sort_order.lower() != "asc" else "ASC"
    per_page = max(1, min(per_page, 200))
    offset = (max(1, page) - 1) * per_page
    rows = get_conn().execute(
        f"SELECT * FROM persons WHERE {clause} ORDER BY {sort_by} {order} LIMIT ? OFFSET ?",
        args + [per_page, offset],
    ).fetchall()
    return [row_to_person(r) for r in rows], total


# --- audit / notifications / announcements -------------------------------------------------
def write_audit(actor: str, action: str, *, person_id: str | None = None,
                related_person_id: str | None = None, meta: dict | None = None) -> None:
    get_conn().execute(
        "INSERT INTO audit_log (id, actor, action, person_id, related_person_id, meta, timestamp)"
        " VALUES (?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), actor, action, person_id, related_person_id,
         json.dumps(meta or {}), _now_iso()),
    )
    get_conn().commit()


def create_notification(ntype: str, *, lost_person_id: str, found_person_id: str,
                        score: float, explanation: str) -> str:
    nid = str(uuid.uuid4())
    get_conn().execute(
        "INSERT INTO notifications (id, type, lost_person_id, found_person_id, score, explanation,"
        " status, created_at) VALUES (?,?,?,?,?,?, 'new', ?)",
        (nid, ntype, lost_person_id, found_person_id, score, explanation, _now_iso()),
    )
    get_conn().commit()
    return nid


def list_notifications(status: str | None = "new", limit: int = 100) -> list[dict]:
    if status:
        rows = get_conn().execute(
            "SELECT * FROM notifications WHERE status=? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = get_conn().execute(
            "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def insert_announcement(person_id: str, target_language: str, text: str, *,
                        triggered_by: str, is_minor_blocked: bool,
                        audio_storage_key: str | None = None) -> str:
    aid = str(uuid.uuid4())
    get_conn().execute(
        "INSERT INTO announcements (id, person_id, target_language, announcement_text,"
        " audio_storage_key, triggered_by, was_broadcast, is_minor_blocked, created_at)"
        " VALUES (?,?,?,?,?,?,0,?,?)",
        (aid, person_id, target_language, text, audio_storage_key, triggered_by,
         1 if is_minor_blocked else 0, _now_iso()),
    )
    get_conn().commit()
    return aid


# --- stats (ops dashboard) -----------------------------------------------------------------
def count_by(column: str) -> dict[str, int]:
    rows = get_conn().execute(f"SELECT {column} k, COUNT(*) c FROM persons GROUP BY {column}").fetchall()
    return {str(r["k"]): r["c"] for r in rows}


def stats_overall() -> dict[str, Any]:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) c FROM persons").fetchone()["c"]
    by_status = count_by("status")
    notif = conn.execute("SELECT COUNT(*) c FROM notifications").fetchone()["c"]
    reunited_pairs = conn.execute(
        "SELECT COUNT(*) c FROM audit_log WHERE action='match_confirmed'"
    ).fetchone()["c"]
    return {
        "total_reports": total,
        "by_status": by_status,
        "notifications": notif,
        "cross_center_matches": reunited_pairs,
    }
