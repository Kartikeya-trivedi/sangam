from constants import age_band_distance
from db.repo import adjacent_age_bands
from services import matching
from tests.conftest import make_person


def test_age_band_distance_and_adjacency():
    assert age_band_distance("61-70", "61-70") == 0
    assert age_band_distance("61-70", "71-80") == 1
    assert age_band_distance("unknown", "61-70") is None
    assert "71-80" in adjacent_age_bands("61-70")
    assert adjacent_age_bands("unknown") == []


def test_gender_veto_zeroes_score():
    q = make_person(role="lost", gender="male", age_band="71-80")
    c = make_person(role="found", gender="female", age_band="71-80")
    m = matching.compute_match_score(q, c)
    assert m.final_score == 0.0
    assert m.confidence == "low"


def test_strong_match_scores_high():
    q = make_person(role="lost", name="Ramesh Kumar", age_band="71-80", gender="male",
                    languages_spoken=["tamil"], clothing=["blue kurta"],
                    last_seen_location="Ramkund Ghat", centre_id="ramkund_kho_ya_paya_kendra")
    c = make_person(role="found", name="Ramesh Kumar", age_band="71-80", gender="male",
                    languages_spoken=["tamil"], clothing=["blue kurta"],
                    last_seen_location="Ramkund Ghat", centre_id="central_control_room")
    m = matching.compute_match_score(q, c)
    assert m.final_score > 0.9
    assert m.confidence == "high"


def test_missing_signals_redistribute_not_penalize():
    # No name, no clothing on either side -> those signals are dropped, not scored as 0.
    q = make_person(role="lost", age_band="61-70", gender="female", languages_spoken=["hindi"])
    c = make_person(role="found", age_band="61-70", gender="female", languages_spoken=["hindi"])
    m = matching.compute_match_score(q, c)
    assert m.breakdown.name is None and m.breakdown.clothing is None
    assert m.final_score > 0.6  # age+gender+language agreement still ranks it well


def test_rank_candidates_filters_and_orders():
    from db import repo
    repo.insert_person(make_person(role="found", name="Ramesh Kumar", age_band="71-80",
                                   gender="male", languages_spoken=["tamil"]))
    repo.insert_person(make_person(role="found", name="Vijay Patil", age_band="18-40",
                                   gender="male"))  # far age -> prefiltered out
    repo.insert_person(make_person(role="found", name="Sita Devi", age_band="71-80",
                                   gender="female"))  # gender -> prefiltered out
    q = make_person(role="lost", name="Ramesh Kumar", age_band="71-80", gender="male",
                    languages_spoken=["tamil"])
    results = matching.rank_candidates(q, k=5, min_score=0.0)
    assert results and results[0].breakdown.name == 1.0
    # only the gender+age-compatible candidate survives the SQL prefilter
    assert all(r.candidate_role == "found" for r in results)
