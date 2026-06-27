from services import geo


def test_dataset_layers_load():
    assert len(geo.zones()) == 32
    assert len(geo.police_stations()) == 14
    assert len(geo.chokepoints()) == 85


def test_geo_proximity_same_and_unknown():
    assert geo.geo_proximity("Ramkund Ghat", "Ramkund Ghat") == (1.0, True)
    score, ok = geo.geo_proximity(None, "Ramkund Ghat")
    assert score == 0.5 and ok is False


def test_geo_proximity_distance_buckets():
    near, _ = geo.geo_proximity("Ramkund Ghat", "Panchavati Circle")     # ~1 km
    far, _ = geo.geo_proximity("Ramkund Ghat", "Trimbakeshwar Approach")  # ~28 km
    assert near > far


def test_nearest_police_to_ramkund():
    p = geo.nearest_police(19.9993, 73.7906)
    assert p and p["km"] < 1.0
