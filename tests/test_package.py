def test_package_import_exposes_node_mappings():
    import __init__ as package
    assert "CivitaiInspirationLoader" in package.NODE_CLASS_MAPPINGS
