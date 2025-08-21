"""Unit tests for protocol constants."""

import pytest
from orion1000_bms.protocol.constants import START, END, PRODUCT_ID_DEFAULT


@pytest.mark.phase1
def test_constants_values() -> None:
    """Test that constants have expected values."""
    assert START == 0xEA
    assert END == 0xF5
    assert PRODUCT_ID_DEFAULT == 0xD1


@pytest.mark.phase1
def test_constants_types() -> None:
    """Test that constants are integers."""
    assert isinstance(START, int)
    assert isinstance(END, int)
    assert isinstance(PRODUCT_ID_DEFAULT, int)
