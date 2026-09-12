from download_api import download_to_output
import pytest

def test_download_rejects_untrusted_url(tmp_path):
    with pytest.raises(ValueError): download_to_output("https://evil.example/x.png", 1, tmp_path)
