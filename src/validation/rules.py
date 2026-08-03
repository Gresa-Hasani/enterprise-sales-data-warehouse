"""
Pure validation functions mirroring the business rules enforced in
sql/staging/*.sql. Kept dependency-free (no DB, no I/O) so they can be
unit tested in isolation.
"""

import re
from datetime import date, datetime

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
KNOWN_CURRENCIES = {"USD", "EUR", "GBP"}


def is_valid_email(email: str | None) -> bool:
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email))


def is_non_negative(value) -> bool:
    if value is None:
        return False
    return float(value) >= 0


def is_known_currency(currency: str | None) -> bool:
    if not currency:
        return False
    return currency in KNOWN_CURRENCIES


def is_future_date(d: date, reference: date | None = None) -> bool:
    reference = reference or date.today()
    return d > reference


def is_positive_quantity(quantity) -> bool:
    if quantity is None:
        return False
    return float(quantity) > 0