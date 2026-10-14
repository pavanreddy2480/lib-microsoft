"""Single state model shared by UI, services, persistence and tests.

CONTRACT FILE - do not change without the integration lead (Person 1) agreeing
and announcing it to the whole team.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Role(str, Enum):
    MEMBER = "MEMBER"
    LIBRARIAN = "LIBRARIAN"


class CopyStatus(str, Enum):
    """Operational state of a physical copy. Only IN_SERVICE can be allocated.

    Time-based availability (reserved / issued for a period) is NOT stored here;
    it is computed from active requests.
    """
    IN_SERVICE = "IN_SERVICE"
    DAMAGED = "DAMAGED"
    UNDER_REPAIR = "UNDER_REPAIR"
    LOST = "LOST"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    RESTRICTED = "RESTRICTED"


class RequestStatus(str, Enum):
    """One request row covers the whole lifecycle: request -> reservation -> loan.

    PENDING   submitted, awaiting librarian review (holds a copy)
    RESERVED  approved = confirmed reservation (holds a copy)
    ISSUED    book handed over = active loan (holds a copy)
    RETURNED  loan closed (copy released)
    REJECTED  review rejected, closed (copy released)
    CANCELLED withdrawn / cancelled before issue, or closed by copy loss (copy released)
    """
    PENDING = "PENDING"
    RESERVED = "RESERVED"
    ISSUED = "ISSUED"
    RETURNED = "RETURNED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


# Statuses that commit a copy for [start_date, end_date] (ISSUED: until returned).
ACTIVE_STATUSES: frozenset[RequestStatus] = frozenset(
    {RequestStatus.PENDING, RequestStatus.RESERVED, RequestStatus.ISSUED}
)

TERMINAL_STATUSES: frozenset[RequestStatus] = frozenset(
    {RequestStatus.RETURNED, RequestStatus.REJECTED, RequestStatus.CANCELLED}
)

# The ONLY source of truth for legal status changes. Services must check this.
ALLOWED_TRANSITIONS: dict[RequestStatus, frozenset[RequestStatus]] = {
    RequestStatus.PENDING: frozenset(
        {RequestStatus.RESERVED, RequestStatus.REJECTED, RequestStatus.CANCELLED}
    ),
    RequestStatus.RESERVED: frozenset({RequestStatus.ISSUED, RequestStatus.CANCELLED}),
    RequestStatus.ISSUED: frozenset({RequestStatus.RETURNED}),
    RequestStatus.RETURNED: frozenset(),
    RequestStatus.REJECTED: frozenset(),
    RequestStatus.CANCELLED: frozenset(),
}

MAX_PERIOD_DAYS = 30  # inclusive: start..end may span at most 30 calendar days


def can_transition(current: RequestStatus, target: RequestStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


@dataclass
class User:
    id: int
    username: str
    full_name: str
    role: Role


@dataclass
class Title:
    id: int
    title: str
    category: str


@dataclass
class Copy:
    id: int
    title_id: int
    copy_code: str
    status: CopyStatus
    note: str = ""


@dataclass
class Request:
    id: int
    member_id: int
    title_id: int
    copy_id: int
    start_date: date
    end_date: date
    status: RequestStatus
    created_at: str
    decision_note: str = ""
    issued_at: str | None = None
    returned_at: str | None = None


@dataclass
class Event:
    """Audit-trail row: every status change (and copy reallocation) writes one."""
    id: int
    request_id: int
    from_status: str | None
    to_status: str
    actor: str
    note: str
    at: str


@dataclass
class AvailabilityResult:
    available: bool
    free_count: int            # in-service copies free for the whole period
    total_in_service: int      # in-service copies of the title
    total_copies: int          # all physical copies of the title
    reason: str = ""           # human-readable explanation when not available
    next_free_date: date | None = None  # earliest date some in-service copy frees up (optional hint)


@dataclass
class TitleAvailability:
    title: Title
    result: AvailabilityResult


@dataclass
class AffectedRequest:
    """Reported when a copy goes out of service and future commitments are handled."""
    request_id: int
    outcome: str               # "MOVED" or "CLOSED"
    old_copy_id: int
    new_copy_id: int | None = None
    message: str = ""
