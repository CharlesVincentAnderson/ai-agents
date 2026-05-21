# test_app.py

import pytest
from app import fizzbuzz


def test_fizzbuzz_returns_1_for_1():
    assert fizzbuzz(1) == "1"


def test_fizzbuzz_returns_2_for_2():
    assert fizzbuzz(2) == "2"


def test_fizzbuzz_returns_fizz_for_3():
    assert fizzbuzz(3) == "Fizz"


def test_fizzbuzz_returns_buzz_for_5():
    assert fizzbuzz(5) == "Buzz"


def test_fizzbuzz_returns_fizz_for_6():
    assert fizzbuzz(6) == "Fizz"


def test_fizzbuzz_returns_buzz_for_10():
    assert fizzbuzz(10) == "Buzz"


def test_fizzbuzz_returns_fizzbuzz_for_15():
    assert fizzbuzz(15) == "FizzBuzz"


def test_fizzbuzz_returns_number_for_non_fizzbuzz_values():
    assert fizzbuzz(7) == "7"
    assert fizzbuzz(8) == "8"


@pytest.mark.parametrize(
    "value,expected",
    [
        (3, "Fizz"),
        (5, "Buzz"),
        (15, "FizzBuzz"),
        (16, "16"),
        (30, "FizzBuzz"),
    ],
)
def test_fizzbuzz_parametrized(value, expected):
    assert fizzbuzz(value) == expected
