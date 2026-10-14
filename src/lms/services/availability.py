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

from lms.domain.clock import business_today
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
    raise NotImplementedError


def effective_end(req: Request, today: date) -> date:
    """ISSUED -> max(req.end_date, today); everything else -> req.end_date."""
    raise NotImplementedError


def validate_period(start: date | None, end: date | None, today: date) -> None:
    """Raise BusinessRuleError, checked in this order:
      - start or end missing       -> INVALID_DATES  "Please choose both a start and a return date."
      - end < start                -> INVALID_DATES  "Return date must be on or after the start date."
      - start < today              -> START_IN_PAST  "Start date cannot be in the past (today is <today>)."
      - (end - start).days + 1 > MAX_PERIOD_DAYS
                                   -> PERIOD_TOO_LONG "Borrowing period is N days; maximum is 30."
    """
    raise NotImplementedError


def is_copy_free(conn: sqlite3.Connection, copy: Copy, start: date, end: date,
                 today: date, exclude_request_id: int | None = None) -> bool:
    """IN_SERVICE and no overlapping active commitment (ignoring exclude_request_id)."""
    raise NotImplementedError


def free_copies(conn: sqlite3.Connection, title_id: int, start: date, end: date,
                exclude_request_id: int | None = None) -> list[Copy]:
    """All copies of the title that are free for the whole period, ordered by copy_code."""
    raise NotImplementedError


def find_free_copy(conn: sqlite3.Connection, title_id: int, start: date, end: date,
                   exclude_request_id: int | None = None) -> Copy | None:
    """First of free_copies(...) or None. Deterministic (lowest copy_code)."""
    raise NotImplementedError


def check_availability(conn: sqlite3.Connection, title_id: int, start: date,
                       end: date) -> AvailabilityResult:
    """Explain availability for the UI and for submit_request's error message.

    reason (when not available) MUST distinguish:
      - "No copies of '<title>' can be lent: all N copies are out of service (damaged / repair / lost / reference-only)."
      - "All K in-service copies of '<title>' are already committed for overlapping dates."
        + " A copy is next free from <date>." when next_free_date can be computed
          (earliest effective_end + 1 day among blocking commitments).
    """
    raise NotImplementedError


def catalog_availability(conn: sqlite3.Connection, start: date,
                         end: date) -> list[TitleAvailability]:
    """check_availability for every title (for the Catalog page)."""
    raise NotImplementedError
