"""Shared test fixtures: isolated temp SQLite DB + external APIs forced offline (free + deterministic)."""
from __future__ import annotations

import uuid

import pytest

from config import settings
from models import Person


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Point every test at a fresh SQLite file and disable Claude/Sarvam so intake is deterministic."""
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(settings, "anthropic_api_key", "")  # force rule-based extraction/rerank
    monkeypatch.setattr(settings, "sarvam_api_key", "")
    import services.claude as claude
    monkeypatch.setattr(claude, "_client", None)
    from db import init_db
    init_db()
    yield


def make_person(**kw) -> Person:
    base = dict(id=str(uuid.uuid4()), role="found", age_band="71-80", gender="male",
                centre_id="central_control_room", consent_given=True)
    base.update(kw)
    return Person(**base)
