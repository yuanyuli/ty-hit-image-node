from cache import Cache

def test_cache_round_trip_and_clear(tmp_path):
    c=Cache(tmp_path)
    c.put("abc", {"items":[1]})
    assert c.get("abc")["items"] == [1]
    c.clear("abc")
    assert c.get("abc") is None
