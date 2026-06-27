from services.names import name_similarity, normalize_name, soundex


def test_normalize_strips_honorifics_and_script():
    assert normalize_name("Shri Ajay Kumar Ji") == "ajay kumar"
    assert normalize_name("  SMT. Lakshmi  ") == "lakshmi"
    assert normalize_name(None) == ""


def test_exact_and_wordorder_match():
    assert name_similarity("Ram Kumar", "Ram Kumar") == 1.0
    assert name_similarity("Ram Kumar", "Kumar Ram") == 1.0  # token-sorted


def test_phonetic_variants_score_mid_high():
    s = name_similarity("Lakshmi", "Laxmi")
    assert s is not None and s > 0.6
    assert soundex("lakshmi") == soundex("laxmi")


def test_missing_name_returns_none():
    assert name_similarity(None, "X") is None
    assert name_similarity("X", "") is None


def test_different_names_score_low():
    s = name_similarity("Ramesh Sharma", "Vijay Patil")
    assert s is not None and s < 0.5
