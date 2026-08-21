from app.nlp import parse_query


def test_parse_keys_azerbaijani():
    parsed = parse_query("Açarımı tap")
    assert parsed.category == "keys"
    assert parsed.wants_find is True


def test_parse_wallet_where():
    parsed = parse_query("cüzdan haradadır?")
    assert parsed.category == "wallet"


def test_parse_empty():
    parsed = parse_query("   ")
    assert parsed.category is None
    assert parsed.wants_find is False
