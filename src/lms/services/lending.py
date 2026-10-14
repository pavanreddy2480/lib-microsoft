"""Lending lifecycle - the state machine.  OWNER: Person 4 (see docs/team/4.md).

Rules for EVERY function here:
  * run inside ONE `with db.transaction() as conn:` block (all-or-nothing)
  * load the request -> NOT_FOUND if missing
  * check models.can_transition(current, target) -> INVALID_TRANSITION otherwise,
    message like "Cannot approve a request that is REJECTED."
  * write repo.insert_event(conn, id, from, to, actor.username, note) for every change
  * use clock.business_today() for "today", never date.today()
  * never edit start/end/title of an existing request (rule 7: create a new one instead)
  * actor is a models.User; librarian-only actions call auth.require_role(actor, Role.LIBRARIAN)
"""
from __future__ import annotations

import sqlite3
from datetime import date

from lms.domain import errors
from lms.domain.clock import business_today
from lms.domain.errors import BusinessRuleError
from lms.domain.models import (
    ACTIVE_STATUSES, AffectedRequest, CopyStatus, Event, Request, RequestStatus, Role, User,
    can_transition,
)
from lms.persistence import db
from lms.persistence import repository as repo
from lms.services import availability
from lms.services.auth import require_role


def submit_request(actor: User, title_id: int, start: date, end: date) -> Request:
    """Member creates a borrowing request (rules R1, R4, R6, R10).

    1. actor must be a MEMBER (NOT_AUTHORIZED otherwise); member_id = actor.id
    2. availability.validate_period(start, end, business_today())
    3. DUPLICATE_REQUEST if this member already has an ACTIVE request for the
       same title overlapping [start, end]
    4. copy = availability.find_free_copy(...); if None ->
       BusinessRuleError(NO_COPY_AVAILABLE, check_availability(...).reason)
    5. insert as PENDING on that copy (the copy is now committed), event None->PENDING
    """
    raise NotImplementedError


def approve_request(actor: User, request_id: int, note: str = "") -> Request:
    """Librarian: PENDING -> RESERVED (confirmed reservation).

    Re-check the allocated copy is still IN_SERVICE; if not, move to another free
    copy (find_free_copy with exclude_request_id) and log it; if none ->
    NO_COPY_AVAILABLE (request stays PENDING so the librarian can reject it).
    """
    raise NotImplementedError


def reject_request(actor: User, request_id: int, reason: str) -> Request:
    """Librarian: PENDING -> REJECTED. reason required (REASON_REQUIRED if blank).
    Status leaves ACTIVE_STATUSES, so the copy is released automatically (rule R7)."""
    raise NotImplementedError


def cancel_request(actor: User, request_id: int, note: str = "") -> Request:
    """PENDING or RESERVED -> CANCELLED (rule R8). Allowed for the owning member
    or a librarian (NOT_AUTHORIZED otherwise). ISSUED cannot be cancelled."""
    raise NotImplementedError


def issue_loan(actor: User, request_id: int) -> Request:
    """Librarian: RESERVED -> ISSUED. Only when start_date <= today <= end_date
    (ISSUE_NOT_ALLOWED otherwise, say which). Sets issued_at."""
    raise NotImplementedError


def return_loan(actor: User, request_id: int,
                condition: CopyStatus = CopyStatus.IN_SERVICE,
                note: str = "") -> tuple[Request, list[AffectedRequest]]:
    """Librarian: ISSUED -> RETURNED, sets returned_at (rule R9).

    If condition != IN_SERVICE the copy status is updated and the copy's other
    future commitments are handled by _handle_copy_out_of_service (same transaction).
    """
    raise NotImplementedError


def set_copy_status(actor: User, copy_id: int, status: CopyStatus,
                    note: str = "") -> list[AffectedRequest]:
    """Librarian inventory action (mark damaged / repaired / lost / ...).

    If the copy currently has an ISSUED loan and status != IN_SERVICE, still allow it
    (the book is out) - but do not touch the ISSUED request.
    If status != IN_SERVICE -> _handle_copy_out_of_service for PENDING/RESERVED.
    """
    raise NotImplementedError


def _handle_copy_out_of_service(conn, actor: User, copy_id: int) -> list[AffectedRequest]:
    """Reallocation policy (user decision): for each PENDING/RESERVED commitment on
    the copy: try find_free_copy(... exclude_request_id=req.id) for the same dates
    -> repo.update_request_copy + event note "moved from X to Y" -> AffectedRequest MOVED;
    else close it (PENDING->REJECTED, RESERVED->CANCELLED) with decision_note
    "Copy <code> became unavailable and no other copy is free for these dates."
    -> AffectedRequest CLOSED. Never silent: everything is returned + logged.
    """
    raise NotImplementedError


# ---------- read helpers for the UI (no transaction needed) ----------
def get_request_history(request_id: int) -> list[Event]:
    """repo.list_events for the request (audit trail shown in the UI)."""
    raise NotImplementedError
