# test_app.py

from app import fizzbuzz


def test_fizzbuzz_1():
    assert fizzbuzz(1) == ["1"]


def test_fizzbuzz_3():
    assert fizzbuzz(3) == ["1", "2", "Fizz"]


def test_fizzbuzz_5():
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]


def test_fizzbuzz_15():
    assert fizzbuzz(15) == [
        "1",
        "2",
        "Fizz",
        "4",
        "Buzz",
        "Fizz",
        "7",
        "8",
        "Fizz",
        "Buzz",
        "11",
        "Fizz",
        "13",
        "14",
        "FizzBuzz",
    ]
