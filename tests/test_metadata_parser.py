from metadata_parser import normalize_item

def test_classifies_b_and_c_without_fabricating_fields():
    b=normalize_item({"id":1,"meta":{"prompt":"a cat","negativePrompt":"bad","steps":20}})
    assert b.classification == "B" and b.prompt == "a cat"
    c=normalize_item({"id":2})
    assert c.classification == "C" and c.prompt == ""
