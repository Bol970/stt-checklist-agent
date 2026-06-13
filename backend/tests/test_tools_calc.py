from app.tools import calc


def test_calc_basic():
    assert calc("5 * 200000 * 3") == {"result": 3000000}


def test_calc_float():
    assert calc("2000000 / 3")["result"] > 666666


def test_calc_unary_and_parens():
    assert calc("-(2 + 3) * 4") == {"result": -20}


def test_calc_rejects_names():
    out = calc("__import__('os').system('echo hi')")
    assert "error" in out


def test_calc_rejects_garbage():
    out = calc("not a number")
    assert "error" in out


def test_calc_power():
    assert calc("2**10") == {"result": 1024}


def test_calc_rejects_huge_exponent():
    out = calc("2**1000000")
    assert "error" in out


def test_calc_rejects_too_long():
    out = calc("1+" * 200 + "1")
    assert "error" in out
