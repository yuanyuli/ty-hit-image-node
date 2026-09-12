from metadata_parser import normalize_item

def test_classifies_b_and_c_without_fabricating_fields():
    b=normalize_item({"id":1,"meta":{"prompt":"a cat","negativePrompt":"bad","steps":20}})
    assert b.classification == "B" and b.prompt == "a cat"
    c=normalize_item({"id":2})
    assert c.classification == "C" and c.prompt == ""

def test_normalize_item_ignores_malformed_metadata():
    result = normalize_item({"id": 1, "meta": "not-an-object"})
    assert result.prompt == ""
    assert result.negative_prompt == ""
    assert result.classification == "C"
