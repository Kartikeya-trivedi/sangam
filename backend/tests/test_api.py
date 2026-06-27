"""End-to-end API smoke tests. Claude/Sarvam are disabled (conftest) -> rule-based extraction."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_and_centres(client):
    h = client.get("/health").json()
    assert h["status"] == "ok"
    assert h["capabilities"]["claude"] is False  # disabled in tests
    assert len(client.get("/api/v1/centres").json()["centres"]) == 10


def test_report_lost_requires_centre(client):
    r = client.post("/api/v1/report/lost", data={"text": "old man"})
    assert r.status_code == 422  # missing required centre_id form field


def test_report_lost_unknown_centre(client):
    r = client.post("/api/v1/report/lost", data={"centre_id": "nope", "text": "old man"})
    assert r.status_code == 400 and "spoken" in r.json()


def test_report_consent_required(client):
    r = client.post("/api/v1/report/lost", data={
        "centre_id": "ramkund_kho_ya_paya_kendra", "text": "old man", "consent_given": "false"})
    assert r.status_code == 403 and r.json()["error"] == "consent_required"


def test_full_lost_then_found_match_and_confirm(client):
    # A family reports a lost elderly man.
    lost = client.post("/api/v1/report/lost", data={
        "centre_id": "ramkund_kho_ya_paya_kendra",
        "text": "elderly man wearing blue kurta speaks tamil"}).json()
    assert lost["structured"]["age_band"] == "71-80"
    assert lost["structured"]["gender"] == "male"

    # A volunteer logs a matching found person at a different centre.
    found = client.post("/api/v1/report/found", data={
        "centre_id": "panchavati_center",
        "text": "elderly man blue kurta tamil"}).json()
    found_id = found["report_id"]

    # Re-running match for the lost report should now surface the found person.
    m = client.get(f"/api/v1/match/{lost['report_id']}", params={"min_score": 0.0}).json()
    ids = [c["candidate_id"] for c in m["candidates"]]
    assert found_id in ids

    # Confirm the reunification.
    c = client.post("/api/v1/ops/confirm", json={
        "lost_person_id": lost["report_id"], "found_person_id": found_id,
        "confirmed_by": "test_staff"})
    assert c.status_code == 200 and c.json()["status"] == "reunited"


def test_minor_announcement_blocked(client):
    rep = client.post("/api/v1/report/found", data={
        "centre_id": "central_control_room", "text": "lost child girl pink frock"}).json()
    assert rep["structured"]["is_minor"] is True
    a = client.post("/api/v1/announce", json={"person_id": rep["report_id"],
                                              "target_language": "hi"})
    assert a.status_code == 403
    assert a.json()["error"] == "minor_announcement_blocked"


def test_adult_announcement_allowed(client):
    rep = client.post("/api/v1/report/found", data={
        "centre_id": "central_control_room", "text": "elderly man white dhoti"}).json()
    a = client.post("/api/v1/announce", json={"person_id": rep["report_id"],
                                              "target_language": "hi"})
    assert a.status_code == 200
    assert a.json()["blocked"] is False and a.json()["announcement_text"]


def test_confirm_minor_requires_guardian_notes(client):
    lost = client.post("/api/v1/report/lost", data={
        "centre_id": "central_control_room", "text": "lost boy school uniform"}).json()
    found = client.post("/api/v1/report/found", data={
        "centre_id": "panchavati_center", "text": "boy school uniform"}).json()
    r = client.post("/api/v1/ops/confirm", json={
        "lost_person_id": lost["report_id"], "found_person_id": found["report_id"],
        "confirmed_by": "staff"})  # no notes
    assert r.status_code == 400 and r.json()["error"] == "guardian_verification_required"


def test_ops_stats_and_map(client):
    assert "by_age_band" in client.get("/api/v1/ops/stats").json()
    fc = client.get("/api/v1/ops/map").json()
    assert fc["type"] == "FeatureCollection" and len(fc["features"]) > 100
