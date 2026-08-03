from datetime import date

from src.validation.rules import (
    is_valid_email,
    is_non_negative,
    is_known_currency,
    is_future_date,
    is_positive_quantity,
)


class TestEmailValidation:
    def test_valid_email(self):
        assert is_valid_email("user@example.com") is True

    def test_invalid_email_missing_at(self):
        assert is_valid_email("user_at_example.com") is False

    def test_invalid_email_none(self):
        assert is_valid_email(None) is False

    def test_invalid_email_empty_string(self):
        assert is_valid_email("") is False


class TestNonNegative:
    def test_positive_value(self):
        assert is_non_negative(10.5) is True

    def test_zero_is_valid(self):
        assert is_non_negative(0) is True

    def test_negative_value_invalid(self):
        assert is_non_negative(-5) is False

    def test_none_is_invalid(self):
        assert is_non_negative(None) is False


class TestCurrency:
    def test_known_currency_usd(self):
        assert is_known_currency("USD") is True

    def test_unknown_currency(self):
        assert is_known_currency("XXX") is False

    def test_none_currency_invalid(self):
        assert is_known_currency(None) is False


class TestFutureDate:
    def test_past_date_not_future(self):
        assert is_future_date(date(2020, 1, 1), reference=date(2026, 1, 1)) is False

    def test_future_date_is_future(self):
        assert is_future_date(date(2027, 1, 1), reference=date(2026, 1, 1)) is True

    def test_same_date_not_future(self):
        d = date(2026, 1, 1)
        assert is_future_date(d, reference=d) is False


class TestQuantity:
    def test_positive_quantity_valid(self):
        assert is_positive_quantity(5) is True

    def test_zero_quantity_invalid(self):
        assert is_positive_quantity(0) is False

    def test_negative_quantity_invalid(self):
        assert is_positive_quantity(-1) is False

    def test_none_quantity_invalid(self):
        assert is_positive_quantity(None) is False