from app import int_to_roman


def test_1():
    assert int_to_roman(1) == "I"


def test_4():
    assert int_to_roman(4) == "IV"


def test_5():
    assert int_to_roman(5) == "V"


def test_9():
    assert int_to_roman(9) == "IX"


def test_10():
    assert int_to_roman(10) == "X"


def test_40():
    assert int_to_roman(40) == "XL"


def test_50():
    assert int_to_roman(50) == "L"


def test_90():
    assert int_to_roman(90) == "XC"


def test_100():
    assert int_to_roman(100) == "C"


def test_400():
    assert int_to_roman(400) == "CD"


def test_500():
    assert int_to_roman(500) == "D"


def test_900():
    assert int_to_roman(900) == "CM"


def test_1000():
    assert int_to_roman(1000) == "M"


def test_1994():
    assert int_to_roman(1994) == "MCMXCIV"


def test_2024():
    assert int_to_roman(2024) == "MMXXIV"


def test_3999():
    assert int_to_roman(3999) == "MMMCMXCIX"
