"""Business date. CONTRACT FILE.

All "today" checks MUST call business_today() - never date.today() directly.
Default is 2026-08-01 so the PDF seed data (Aug 2026) is meaningful; the
Streamlit sidebar can override it for demos ("move time forward").
"""
from datetime import date

DEFAULT_BUSINESS_DATE = date(2026, 8, 1)

_today: date = DEFAULT_BUSINESS_DATE


def business_today() -> date:
    return _today


def set_business_today(d: date) -> None:
    global _today
    _today = d


def reset_business_today() -> None:
    set_business_today(DEFAULT_BUSINESS_DATE)
