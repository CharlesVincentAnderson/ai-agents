import pytest

from app import calculate


def test_calculate_add():
    assert calculate("add", 2, 3) == 5


def test_calculate_subtract():
    assert calculate("subtract", 10, 4) == 6


def test_calculate_multiply():
    assert calculate("multiply", 3, 5) == 15


def test_calculate_divide():
    assert calculate("divide", 20, 4) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError, match="division by zero"):
        calculate("divide", 10, 0)


def test_invalid_operation():
    with pytest.raises(ValueError, match="unsupported operation"):
        calculate("modulus", 10, 3)
