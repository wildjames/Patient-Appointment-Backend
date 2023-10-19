import pytest
from ..utils import validators


@pytest.mark.parametrize(
    "nhs_number, expected",
    [
        ("0123456789", True),
        ("0123456780", False),
        ("1122334451", True),
        ("1122334455", False),
        ("123456789a", False),  # Contains a non-numeric character
        ("123456789", False),  # Less than 10 digits
        ("12345678901", False),  # More than 10 digits
    ],
)
def test_validate_nhs_number(nhs_number, expected):
    result = validators.validate_nhs_number(nhs_number)
    assert (
        result == expected
    ), f"For NHS number: {nhs_number}, expected: {expected} but got: {result}"
