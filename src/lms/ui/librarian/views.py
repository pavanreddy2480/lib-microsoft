"""View models (DTOs) for the librarian pages.

Frozen, UI-shaped data: names already resolved, no repository objects leak into
the pages. Pure data, no I/O, so presenters and tests can build them freely.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from lms.domain.models import CopyStatus, RequestStatus


@dataclass(frozen=True)
class RequestRow:
    id: int
    member_name: str
    title: str
    copy_code: str
    start_date: date
    end_date: date
    status: RequestStatus
    created_at: str
    decision_note: str = ""


@dataclass(frozen=True)
class CopyRow:
    id: int
    title: str
    copy_code: str
    status: CopyStatus
    note: str = ""
    commitment: str = ""  # human text for the earliest active commitment, "" if none


@dataclass(frozen=True)
class AffectedRow:
    request_id: int
    outcome: str  # "MOVED" | "CLOSED"
    message: str


@dataclass(frozen=True)
class ReturnOutcome:
    request: RequestRow
    affected: tuple[AffectedRow, ...] = ()
