from gemini_demo import extract_text

def test_extract_test():
    data = {"candidates": [{"content": {"parts": [{"text": "ciao"}]}}]}
    assert extract_text(data) == "ciao"