from app.services.model_service import _clean_text


def test_clean_text_lowercases():
    assert _clean_text("HELLO World") == "hello world"


def test_clean_text_removes_redaction_placeholders():
    # CFPB's XXXX-style redaction should be replaced, not kept as literal x's
    result = _clean_text("my account XXXX was charged")
    assert "xxxx" not in result
    assert "account" in result and "charged" in result


def test_clean_text_strips_punctuation_and_digits():
    result = _clean_text("I was charged $450 on 3/3/2024!")
    assert "$" not in result
    assert "450" not in result
    assert "charged" in result


def test_clean_text_collapses_whitespace():
    result = _clean_text("too    many     spaces")
    assert "  " not in result  # no double spaces survive