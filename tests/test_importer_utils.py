import pytest

from importer import detect_country_enhanced, is_travel_day


@pytest.mark.parametrize(
    "cell_text,expected",
    [
        ("tr-UK", "UK"),
        ("TR-UK", "UK"),
        ("tr-GB", "UK"),
        ("UK", "UK"),
        ("GB", "UK"),
        ("tr-DE", "DE"),
    ],
)
def test_detect_country_enhanced_handles_travel_day_markers(cell_text, expected):
    """Cells with travel-day prefixes should still detect the underlying country."""
    assert detect_country_enhanced(cell_text) == expected


@pytest.mark.parametrize(
    "cell_text,expected",
    [
        ("tr-UK", True),
        ("tr-DE", True),
        ("Tr", True),
        ("travel", False),
        ("DE", False),
    ],
)
def test_is_travel_day(cell_text, expected):
    assert is_travel_day(cell_text) == expected
