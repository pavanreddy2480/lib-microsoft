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
    require_role(actor, Role.MEMBER)
    with db.transaction() as conn:
        today = business_today()
        availability.validate_period(start, end, today)
        for existing in repo.active_commitments_for_title(conn, title_id):
            if existing.member_id == actor.id and availability.overlaps(
                existing.start_date, existing.end_date, start, end
            ):
                raise BusinessRuleError(
                    errors.DUPLICATE_REQUEST,
                    "You already have an overlapping active request for this title.",
                )

        copy = availability.find_free_copy(conn, title_id, start, end)
        if copy is None:
            result = availability.check_availability(conn, title_id, start, end)
            raise BusinessRuleError(errors.NO_COPY_AVAILABLE, result.reason)
        try:
            request_id = repo.insert_request(
                conn, actor.id, title_id, copy.id, start, end, RequestStatus.PENDING
            )
        except sqlite3.IntegrityError as exc:
            if "COPY_OVERLAP" not in str(exc):
                raise
            result = availability.check_availability(conn, title_id, start, end)
            raise BusinessRuleError(errors.NO_COPY_AVAILABLE, result.reason) from exc
        repo.insert_event(conn, request_id, None, RequestStatus.PENDING.value, actor.username)
        return repo.get_request(conn, request_id)


def approve_request(actor: User, request_id: int, note: str = "") -> Request:
    """Librarian: PENDING -> RESERVED (confirmed reservation).

    Re-check the allocated copy is still IN_SERVICE; if not, move to another free
    copy (find_free_copy with exclude_request_id) and log it; if none ->
    NO_COPY_AVAILABLE (request stays PENDING so the librarian can reject it).
    """
    require_role(actor, Role.LIBRARIAN)
    with db.transaction() as conn:
        req = _load(conn, request_id)
        _check_transition(req, RequestStatus.RESERVED, "approve")
        copy = repo.get_copy(conn, req.copy_id)
        if copy is None or copy.status != CopyStatus.IN_SERVICE:
            replacement = availability.find_free_copy(
                conn, req.title_id, req.start_date, req.end_date,
                exclude_request_id=req.id,
            )
            if replacement is None:
                result = availability.check_availability(
                    conn, req.title_id, req.start_date, req.end_date
                )
                raise BusinessRuleError(errors.NO_COPY_AVAILABLE, result.reason)
            repo.update_request_copy(conn, req.id, replacement.id)
            repo.insert_event(
                conn, req.id, req.status.value, req.status.value, actor.username,
                f"moved from {copy.copy_code if copy else req.copy_id} to {replacement.copy_code}",
            )
        repo.update_request_status(
            conn, req.id, RequestStatus.RESERVED, decision_note=note
        )
        repo.insert_event(
            conn, req.id, req.status.value, RequestStatus.RESERVED.value,
            actor.username, note,
        )
        return repo.get_request(conn, req.id)


def reject_request(actor: User, request_id: int, reason: str) -> Request:
    """Librarian: PENDING -> REJECTED. reason required (REASON_REQUIRED if blank).
    Status leaves ACTIVE_STATUSES, so the copy is released automatically (rule R7)."""
    require_role(actor, Role.LIBRARIAN)
    if not reason.strip():
        raise BusinessRuleError(errors.REASON_REQUIRED, "A rejection reason is required.")
    with db.transaction() as conn:
        req = _load(conn, request_id)
        _check_transition(req, RequestStatus.REJECTED, "reject")
        repo.update_request_status(
            conn, req.id, RequestStatus.REJECTED, decision_note=reason
        )
        repo.insert_event(
            conn, req.id, req.status.value, RequestStatus.REJECTED.value,
            actor.username, reason,
        )
        return repo.get_request(conn, req.id)


def cancel_request(actor: User, request_id: int, note: str = "") -> Request:
    """PENDING or RESERVED -> CANCELLED (rule R8). Allowed for the owning member
    or a librarian (NOT_AUTHORIZED otherwise). ISSUED cannot be cancelled."""
    with db.transaction() as conn:
        req = _load(conn, request_id)
        if actor.role != Role.LIBRARIAN and req.member_id != actor.id:
            raise BusinessRuleError(
                errors.NOT_AUTHORIZED, "Only the request owner or a librarian may cancel it."
            )
        _check_transition(req, RequestStatus.CANCELLED, "cancel")
        repo.update_request_status(
            conn, req.id, RequestStatus.CANCELLED, decision_note=note
        )
        repo.insert_event(
            conn, req.id, req.status.value, RequestStatus.CANCELLED.value,
            actor.username, note,
        )
        return repo.get_request(conn, req.id)


def issue_loan(actor: User, request_id: int) -> Request:
    """Librarian: RESERVED -> ISSUED. Only when start_date <= today <= end_date
    (ISSUE_NOT_ALLOWED otherwise, say which). Sets issued_at."""
    require_role(actor, Role.LIBRARIAN)
    with db.transaction() as conn:
        req = _load(conn, request_id)
        _check_transition(req, RequestStatus.ISSUED, "issue")
        today = business_today()
        if today < req.start_date:
            raise BusinessRuleError(
                errors.ISSUE_NOT_ALLOWED,
                f"Cannot issue before the start date ({req.start_date:%d %b %Y}).",
            )
        if today > req.end_date:
            raise BusinessRuleError(
                errors.ISSUE_NOT_ALLOWED,
                f"Reservation period ended on {req.end_date:%d %b %Y}; cancel it instead.",
            )
        issued_at = repo.now_ts()
        repo.update_request_status(
            conn, req.id, RequestStatus.ISSUED, issued_at=issued_at
        )
        repo.insert_event(
            conn, req.id, req.status.value, RequestStatus.ISSUED.value, actor.username
        )
        return repo.get_request(conn, req.id)


def return_loan(actor: User, request_id: int,
                condition: CopyStatus = CopyStatus.IN_SERVICE,
                note: str = "") -> tuple[Request, list[AffectedRequest]]:
    """Librarian: ISSUED -> RETURNED, sets returned_at (rule R9).

    If condition != IN_SERVICE the copy status is updated and the copy's other
    future commitments are handled by _handle_copy_out_of_service (same transaction).
    """
    require_role(actor, Role.LIBRARIAN)
    with db.transaction() as conn:
        req = _load(conn, request_id)
        _check_transition(req, RequestStatus.RETURNED, "return")
        returned_at = repo.now_ts()
        repo.update_request_status(
            conn, req.id, RequestStatus.RETURNED, returned_at=returned_at,
            decision_note=note,
        )
        repo.insert_event(
            conn, req.id, req.status.value, RequestStatus.RETURNED.value,
            actor.username, note,
        )
        affected: list[AffectedRequest] = []
        repo.update_copy_status(conn, req.copy_id, condition, note)
        if condition != CopyStatus.IN_SERVICE:
            affected = _handle_copy_out_of_service(conn, actor, req.copy_id)
        return repo.get_request(conn, req.id), affected


def set_copy_status(actor: User, copy_id: int, status: CopyStatus,
                    note: str = "") -> list[AffectedRequest]:
    """Librarian inventory action (mark damaged / repaired / lost / ...).

    If the copy currently has an ISSUED loan and status != IN_SERVICE, still allow it
    (the book is out) - but do not touch the ISSUED request.
    If status != IN_SERVICE -> _handle_copy_out_of_service for PENDING/RESERVED.
    """
    require_role(actor, Role.LIBRARIAN)
    with db.transaction() as conn:
        copy = repo.get_copy(conn, copy_id)
        if copy is None:
            raise BusinessRuleError(errors.NOT_FOUND, f"Copy {copy_id} was not found.")
        repo.update_copy_status(conn, copy_id, status, note)
        if status == CopyStatus.IN_SERVICE:
            return []
        return _handle_copy_out_of_service(conn, actor, copy_id)


def _handle_copy_out_of_service(conn, actor: User, copy_id: int) -> list[AffectedRequest]:
    """Reallocation policy (user decision): for each PENDING/RESERVED commitment on
    the copy: try find_free_copy(... exclude_request_id=req.id) for the same dates
    -> repo.update_request_copy + event note "moved from X to Y" -> AffectedRequest MOVED;
    else close it (PENDING->REJECTED, RESERVED->CANCELLED) with decision_note
    "Copy <code> became unavailable and no other copy is free for these dates."
    -> AffectedRequest CLOSED. Never silent: everything is returned + logged.
    """
    copy = repo.get_copy(conn, copy_id)
    if copy is None:
        raise BusinessRuleError(errors.NOT_FOUND, f"Copy {copy_id} was not found.")
    affected: list[AffectedRequest] = []
    for req in repo.active_commitments_for_copy(conn, copy_id):
        if req.status == RequestStatus.ISSUED:
            continue
        replacement = availability.find_free_copy(
            conn, req.title_id, req.start_date, req.end_date,
            exclude_request_id=req.id,
        )
        if replacement is not None:
            repo.update_request_copy(conn, req.id, replacement.id)
            message = f"moved from {copy.copy_code} to {replacement.copy_code}"
            repo.insert_event(
                conn, req.id, req.status.value, req.status.value,
                actor.username, message,
            )
            affected.append(AffectedRequest(
                req.id, "MOVED", copy_id, replacement.id, message
            ))
            continue

        target = (
            RequestStatus.REJECTED
            if req.status == RequestStatus.PENDING
            else RequestStatus.CANCELLED
        )
        if not can_transition(req.status, target):
            continue
        message = (
            f"Copy {copy.copy_code} became unavailable and no other copy is free "
            "for these dates."
        )
        repo.update_request_status(
            conn, req.id, target, decision_note=message
        )
        repo.insert_event(
            conn, req.id, req.status.value, target.value, actor.username, message
        )
        affected.append(AffectedRequest(req.id, "CLOSED", copy_id, None, message))
    return affected


# ---------- read helpers for the UI (no transaction needed) ----------
def get_request_history(request_id: int) -> list[Event]:
    """repo.list_events for the request (audit trail shown in the UI)."""
    with db.transaction() as conn:
        if repo.get_request(conn, request_id) is None:
            raise BusinessRuleError(errors.NOT_FOUND, f"Request {request_id} was not found.")
        return repo.list_events(conn, request_id)


def _load(conn, request_id: int) -> Request:
    request = repo.get_request(conn, request_id)
    if request is None:
        raise BusinessRuleError(errors.NOT_FOUND, f"Request {request_id} was not found.")
    return request


def _check_transition(req: Request, target: RequestStatus, verb: str) -> None:
    if not can_transition(req.status, target):
        raise BusinessRuleError(
            errors.INVALID_TRANSITION,
            f"Cannot {verb} a request that is {req.status.value}.",
        )
