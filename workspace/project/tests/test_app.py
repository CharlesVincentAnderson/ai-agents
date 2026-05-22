from app import is_palindrome


def test_simple_palindrome():
    assert is_palindrome("racecar") is True


def test_simple_non_palindrome():
    assert is_palindrome("hello") is False


def test_mixed_case_palindrome():
    assert is_palindrome("RaceCar") is True


def test_palindrome_with_spaces():
    assert is_palindrome("nurses run") is True


def test_palindrome_with_punctuation():
    assert is_palindrome("A man, a plan, a canal: Panama!") is True


def test_empty_string():
    assert is_palindrome("") is True


def test_single_character():
    assert is_palindrome("a") is True


def test_numeric_palindrome():
    assert is_palindrome("12321") is True


def test_numeric_non_palindrome():
    assert is_palindrome("12345") is False
