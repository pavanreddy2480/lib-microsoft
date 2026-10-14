"""Availability engine - the heart of rules R2-R5, R10.  OWNER: Person 3 (see docs/team/3.md).

Availability is computed per PHYSICAL COPY, never from a title-level counter.
A copy can be allocated for [start, end] iff:
  1. copy.status == IN_SERVICE, and
  2. no ACTIVE request on that copy overlaps [start, end]
     (overlap is inclusive: a.start <= b.end and b.start <= a.end;
      an ISSUED request blocks until max(end_date, business_today()) - overdue loans
      keep the copy until actually returned).
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from lms.domain import clock
from lms.domain.errors import (
    INVALID_DATES, PERIOD_TOO_LONG, START_IN_PAST, BusinessRuleError,
)
from lms.domain.models import (
    MAX_PERIOD_DAYS, AvailabilityResult, Copy, CopyStatus, Request, RequestStatus,
    TitleAvailability,
)
from lms.persistence import repository as repo


def overlaps(s1: date, e1: date, s2: date, e2: date) -> bool:
    """Inclusive date-range overlap."""
    return s1 <= e2 and s2 <= e1


def effective_end(req: Request, today: date) -> date:
    """ISSUED -> max(req.end_date, today); everything else -> req.end_date."""
    if req.status == RequestStatus.ISSUED:
        return max(req.end_date, today)
    return req.end_date


def validate_period(start: date | None, end: date | None, today: date) -> None:
    """Raise BusinessRuleError, checked in this order:
      - start or end missing       -> INVALID_DATES  "Please choose both a start and a return date."
      - end < start                -> INVALID_DATES  "Return date must be on or after the start date."
      - start < today              -> START_IN_PAST  "Start date cannot be in the past (today is <today>)."
      - (end - start).days + 1 > MAX_PERIOD_DAYS
                                   -> PERIOD_TOO_LONG "Borrowing period is N days; maximum is 30."
    """
    if start is None or end is None:
        raise BusinessRuleError(
            INVALID_DATES, "Please choose both a start and a return date."
        )
    if end < start:
        raise BusinessRuleError(
            INVALID_DATES, "Return date must be on or after the start date."
        )
    if start < today:
        raise BusinessRuleError(
            START_IN_PAST,
            f"Start date cannot be in the past (today is {today:%d %b %Y}).",
        )
    period_days = (end - start).days + 1
    if period_days > MAX_PERIOD_DAYS:
        raise BusinessRuleError(
            PERIOD_TOO_LONG,
            f"Borrowing period is {period_days} days; maximum is {MAX_PERIOD_DAYS}.",
        )


def is_copy_free(conn: sqlite3.Connection, copy: Copy, start: date, end: date,
                 today: date, exclude_request_id: int | None = None) -> bool:
    """IN_SERVICE and no overlapping active commitment (ignoring exclude_request_id)."""
    if copy.status != CopyStatus.IN_SERVICE:
        return False
    for request in repo.active_commitments_for_copy(conn, copy.id):
        if request.id != exclude_request_id and overlaps(
            start, end, request.start_date, effective_end(request, today)
        ):
            return False
    return True


def free_copies(conn: sqlite3.Connection, title_id: int, start: date, end: date,
                exclude_request_id: int | None = None) -> list[Copy]:
    """All copies of the title that are free for the whole period, ordered by copy_code."""
    today = clock.business_today()
    return [
        copy
        for copy in repo.list_copies(conn, title_id)
        if is_copy_free(conn, copy, start, end, today, exclude_request_id)
    ]


def find_free_copy(conn: sqlite3.Connection, title_id: int, start: date, end: date,
                   exclude_request_id: int | None = None) -> Copy | None:
    """First of free_copies(...) or None. Deterministic (lowest copy_code)."""
    copies = free_copies(conn, title_id, start, end, exclude_request_id)
    return copies[0] if copies else None


def check_availability(conn: sqlite3.Connection, title_id: int, start: date,
                       end: date) -> AvailabilityResult:
    """Explain availability for the UI and for submit_request's error message.

    reason (when not available) MUST distinguish:
      - "No copies of '<title>' can be lent: all N copies are out of service (damaged / repair / lost / reference-only)."
      - "All K in-service copies of '<title>' are already committed for overlapping dates."
        + " A copy is next free from <date>." when next_free_date can be computed
          (earliest effective_end + 1 day among blocking commitments).
    """
    today = clock.business_today()
    validate_period(start, end, today)

    title = repo.get_title(conn, title_id)
    copies = repo.list_copies(conn, title_id)
    in_service = [copy for copy in copies if copy.status == CopyStatus.IN_SERVICE]
    free_count = sum(
        is_copy_free(conn, copy, start, end, today) for copy in in_service
    )
    if free_count:
        return AvailabilityResult(
            available=True,
            free_count=free_count,
            total_in_service=len(in_service),
            total_copies=len(copies),
        )

    title_name = title.title if title else str(title_id)
    if not in_service:
        reason = (
            f"No copies of '{title_name}' can be lent: all {len(copies)} copies "
            "are out of service (damaged / repair / lost / reference-only)."
        )
        next_free_date = None
    else:
        blocking_ends = [
            effective_end(request, today)
            for copy in in_service
            for request in repo.active_commitments_for_copy(conn, copy.id)
            if overlaps(start, end, request.start_date, effective_end(request, today))
        ]
        next_free_date = min(blocking_ends) + timedelta(days=1) if blocking_ends else None
        reason = (
            f"All {len(in_service)} in-service copies of '{title_name}' are already "
            "committed for overlapping dates."
        )
        if next_free_date is not None:
            reason += f" A copy is next free from {next_free_date:%d %b %Y}."

    return AvailabilityResult(
        available=False,
        free_count=0,
        total_in_service=len(in_service),
        total_copies=len(copies),
        reason=reason,
        next_free_date=next_free_date,
    )


def catalog_availability(conn: sqlite3.Connection, start: date,
                         end: date) -> list[TitleAvailability]:
    """check_availability for every title (for the Catalog page)."""
    return [
        TitleAvailability(title=title, result=check_availability(conn, title.id, start, end))
        for title in repo.list_titles(conn)
    ]
