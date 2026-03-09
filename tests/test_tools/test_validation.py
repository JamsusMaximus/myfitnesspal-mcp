"""Tests for input validation models."""

import pytest
from pydantic import ValidationError

from mfp_mcp.tools._validation import DateInput, DateRangeInput, FoodSearchInput, MeasurementInput, format_validation_error


class TestDateInput:
    def test_valid_date_string(self):
        d = DateInput(date="2026-03-09")
        assert d.date.isoformat() == "2026-03-09"

    def test_invalid_date_string(self):
        with pytest.raises(ValidationError):
            DateInput(date="not-a-date")


class TestDateRangeInput:
    def test_valid_range(self):
        r = DateRangeInput(start_date="2026-03-01", end_date="2026-03-10")
        assert r.start_date.isoformat() == "2026-03-01"

    def test_reversed_dates(self):
        with pytest.raises(ValidationError, match="before or equal"):
            DateRangeInput(start_date="2026-03-10", end_date="2026-03-01")

    def test_too_large_range(self):
        with pytest.raises(ValidationError, match="Maximum 31 days"):
            DateRangeInput(start_date="2026-01-01", end_date="2026-03-01")


class TestMeasurementInput:
    def test_defaults(self):
        m = MeasurementInput()
        assert m.measurement == "Weight"
        assert m.start_date is None

    def test_reversed_dates(self):
        with pytest.raises(ValidationError, match="before"):
            MeasurementInput(start_date="2026-03-10", end_date="2026-03-01")


class TestFoodSearchInput:
    def test_valid(self):
        f = FoodSearchInput(query="chicken")
        assert f.query == "chicken"

    def test_empty_rejects(self):
        with pytest.raises(ValidationError):
            FoodSearchInput(query="")


class TestFormatValidationError:
    def test_formats_error(self):
        try:
            DateInput(date="bad")
        except ValidationError as e:
            msg = format_validation_error(e)
            assert "date" in msg
