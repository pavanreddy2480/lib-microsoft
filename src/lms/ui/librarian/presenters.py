"""Pure presentation logic: no Streamlit, no database. Fully unit-testable.

Anything a page needs to *decide* (ordering, overdue, filtering, wording, which
severity an outcome gets) lives here so the pages stay declarative.
"""
from __future__ import annotations

from datetime import date
from typing import Callable, Iterable, Sequence

from lms.domain.models import Event, Request, RequestStatus
from lms.ui.librarian.views import AffectedRow, RequestRow

DATE_FMT = "%d %b %Y"

# Strategy table: outcome -> UI severity. A new outcome only needs a new entry.
OUTCOME_SEVERITY = {"MOVED": "info", "CLOSED": "warning"}


def fmt_period(start: date, end: date) -> str:
    return f"{start.strftime(DATE_FMT)} → {end.strftime(DATE_FMT)}"


def oldest_first(rows: Iterable[RequestRow]) -> list[RequestRow]:
    """Review queue order: earliest submission first (ids grow with time)."""
    return sorted(rows, key=lambda r: r.id)


def is_overdue(row: RequestRow, today: date) -> bool:
    """An ISSUED loan past its end date and still not returned."""
    return row.status is RequestStatus.ISSUED and row.end_date < today


def only(rows: Iterable[RequestRow], status: RequestStatus) -> list[RequestRow]:
    return [r for r in rows if r.status is status]


def filter_by_status(rows: Iterable[RequestRow],
                     statuses: Sequence[RequestStatus]) -> list[RequestRow]:
    wanted = set(statuses)
    return [r for r in rows if r.status in wanted]


def request_headline(row: RequestRow) -> str:
    return f"#{row.id} · {row.title}"


def request_details(row: RequestRow) -> str:
    return (f"Member: {row.member_name} · Copy: {row.copy_code} · "
            f"Period: {fmt_period(row.start_date, row.end_date)} · "
            f"Submitted: {row.created_at}")


def requests_table(rows: Iterable[RequestRow], today: date) -> list[dict]:
    """Records for st.dataframe, newest first."""
    return [
        {
            "ID": r.id,
            "Member": r.member_name,
            "Title": r.title,
            "Copy": r.copy_code,
            "From": r.start_date,
            "To": r.end_date,
            "Status": "OVERDUE" if is_overdue(r, today) else r.status.value,
            "Note": r.decision_note,
        }
        for r in sorted(rows, key=lambda r: r.id, reverse=True)
    ]


def outcome_severity(row: AffectedRow) -> str:
    return OUTCOME_SEVERITY.get(row.outcome, "warning")


def affected_text(row: AffectedRow) -> str:
    return f"Request #{row.request_id} {row.outcome}: {row.message}"


def describe_commitment(commitments: Sequence[Request],
                        member_name: Callable[[Request], str]) -> str:
    """Earliest active commitment of a copy as text, e.g. 'RESERVED 04 Aug 2026 → 08 Aug 2026 (Meera)'."""
    if not commitments:
        return ""
    first = min(commitments, key=lambda r: (r.start_date, r.id))
    return f"{first.status.value} {fmt_period(first.start_date, first.end_date)} ({member_name(first)})"


def history_table(events: Iterable[Event]) -> list[dict]:
    return [
        {"At": e.at, "From": e.from_status or "-", "To": e.to_status,
         "By": e.actor, "Note": e.note}
        for e in events
    ]
