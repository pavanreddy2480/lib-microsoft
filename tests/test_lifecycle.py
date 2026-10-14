from datetime import date

import pytest

from lms.domain import clock, errors
from lms.domain.models import CopyStatus, RequestStatus
from lms.persistence import repository as repo
from lms.services import availability, lending

D = date
START, END = D(2026, 8, 5), D(2026, 8, 12)


@pytest.fixture
def pending(asha, title_id):
    return lending.submit_request(asha, title_id("Database System Concepts"), START, END)


@pytest.fixture
def reserved(pending, librarian):
    return lending.approve_request(librarian, pending.id)


@pytest.fixture
def issued(reserved, librarian):
    clock.set_business_today(START)
    return lending.issue_loan(librarian, reserved.id)


def assert_refused(conn, code, action):
    """Refused actions must preserve all persisted requests, copies and events."""
    def snapshot():
        return tuple(tuple(tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY id"))
                     for table in ("requests", "copies", "request_events"))
    before = snapshot()
    with pytest.raises(errors.BusinessRuleError) as caught:
        action()
    assert caught.value.code == code
    assert caught.value.message
    assert snapshot() == before


def test_happy_path_and_audit(conn, asha, librarian, title_id):
    tid = title_id("Database System Concepts")
    original = availability.check_availability(conn, tid, START, END).free_count
    request = lending.submit_request(asha, tid, START, END)
    assert request.status == RequestStatus.PENDING
    assert (request.member_id, request.title_id, request.start_date, request.end_date) == (asha.id, tid, START, END)
    assert availability.check_availability(conn, tid, START, END).free_count == original - 1
    approved = lending.approve_request(librarian, request.id, "Approved for coursework")
    assert approved.status == RequestStatus.RESERVED
    clock.set_business_today(START)
    loan = lending.issue_loan(librarian, request.id)
    assert loan.status == RequestStatus.ISSUED
    assert loan.issued_at
    returned, affected = lending.return_loan(librarian, request.id)
    assert returned.status == RequestStatus.RETURNED
    assert returned.returned_at
    assert affected == []
    stored = repo.get_request(conn, request.id)
    assert stored.status == RequestStatus.RETURNED
    assert (stored.member_id, stored.title_id, stored.start_date, stored.end_date) == (asha.id, tid, START, END)
    assert availability.check_availability(conn, tid, START, END).free_count == original
    history = lending.get_request_history(request.id)
    assert len(history) == 4
    assert [(e.from_status, e.to_status, e.actor) for e in history] == [
        (None, "PENDING", asha.username),
        ("PENDING", "RESERVED", librarian.username),
        ("RESERVED", "ISSUED", librarian.username),
        ("ISSUED", "RETURNED", librarian.username),
    ]
    assert all(e.at and e.request_id == request.id for e in history)


def test_reject_releases_last_copy(conn, asha, ravi, librarian, title_id):
    tid = title_id("Design Patterns")
    request = lending.submit_request(asha, tid, START, END)
    result = lending.reject_request(librarian, request.id, "Please choose different dates")
    assert result.status == RequestStatus.REJECTED
    assert result.decision_note == "Please choose different dates"
    assert len(lending.get_request_history(request.id)) == 2
    replacement = lending.submit_request(ravi, tid, START, END)
    assert replacement.copy_id == request.copy_id


@pytest.mark.parametrize("reason", ["", "   ", "\t\n"])
def test_rejection_requires_reason(conn, pending, librarian, reason):
    assert_refused(conn, errors.REASON_REQUIRED,
                   lambda: lending.reject_request(librarian, pending.id, reason))


@pytest.mark.parametrize("approve", [False, True])
@pytest.mark.parametrize("actor_name", ["owner", "librarian"])
def test_cancel_releases_copy(conn, asha, ravi, librarian, title_id, approve, actor_name):
    tid = title_id("Design Patterns")
    request = lending.submit_request(asha, tid, START, END)
    if approve:
        lending.approve_request(librarian, request.id)
    actor = asha if actor_name == "owner" else librarian
    cancelled = lending.cancel_request(actor, request.id, "Plans changed")
    assert cancelled.status == RequestStatus.CANCELLED
    assert len(lending.get_request_history(request.id)) == (3 if approve else 2)
    assert lending.submit_request(ravi, tid, START, END).copy_id == request.copy_id


def test_cannot_cancel_issued(conn, issued, asha):
    assert_refused(conn, errors.INVALID_TRANSITION, lambda: lending.cancel_request(asha, issued.id))


def test_cannot_issue_before_review(conn, pending, librarian):
    clock.set_business_today(START)
    assert_refused(conn, errors.INVALID_TRANSITION, lambda: lending.issue_loan(librarian, pending.id))


def test_other_member_cannot_cancel(conn, pending, ravi):
    assert_refused(conn, errors.NOT_AUTHORIZED, lambda: lending.cancel_request(ravi, pending.id))


@pytest.mark.parametrize("action", ["approve", "reject", "issue", "return", "inventory"])
def test_member_cannot_perform_librarian_action(conn, issued, asha, action):
    calls = {
        "approve": lambda: lending.approve_request(asha, issued.id),
        "reject": lambda: lending.reject_request(asha, issued.id, "Reason"),
        "issue": lambda: lending.issue_loan(asha, issued.id),
        "return": lambda: lending.return_loan(asha, issued.id),
        "inventory": lambda: lending.set_copy_status(asha, issued.copy_id, CopyStatus.DAMAGED),
    }
    assert_refused(conn, errors.NOT_AUTHORIZED, calls[action])


def test_librarian_cannot_submit_member_request(conn, librarian, title_id):
    assert_refused(conn, errors.NOT_AUTHORIZED,
                   lambda: lending.submit_request(librarian, title_id("Database System Concepts"), START, END))


@pytest.mark.parametrize("today", [D(2026, 8, 4), D(2026, 8, 13)])
def test_issue_outside_dates(conn, reserved, librarian, today):
    clock.set_business_today(today)
    assert_refused(conn, errors.ISSUE_NOT_ALLOWED, lambda: lending.issue_loan(librarian, reserved.id))


@pytest.mark.parametrize("today", [START, END])
def test_issue_on_inclusive_boundary(reserved, librarian, today):
    clock.set_business_today(today)
    assert lending.issue_loan(librarian, reserved.id).status == RequestStatus.ISSUED


@pytest.mark.parametrize("terminal", ["reject", "cancel", "return"])
@pytest.mark.parametrize("action", ["approve", "reject", "cancel", "issue", "return"])
def test_terminal_requests_cannot_reopen(conn, pending, librarian, terminal, action):
    if terminal == "reject":
        lending.reject_request(librarian, pending.id, "Closed")
    elif terminal == "cancel":
        lending.cancel_request(librarian, pending.id)
    else:
        lending.approve_request(librarian, pending.id)
        clock.set_business_today(START)
        lending.issue_loan(librarian, pending.id)
        lending.return_loan(librarian, pending.id)
    calls = {
        "approve": lambda: lending.approve_request(librarian, pending.id),
        "reject": lambda: lending.reject_request(librarian, pending.id, "Closed"),
        "cancel": lambda: lending.cancel_request(librarian, pending.id),
        "issue": lambda: lending.issue_loan(librarian, pending.id),
        "return": lambda: lending.return_loan(librarian, pending.id),
    }
    assert_refused(conn, errors.INVALID_TRANSITION, calls[action])


@pytest.mark.parametrize("action", ["approve", "reject", "cancel", "issue", "return"])
def test_unknown_request(conn, librarian, action):
    calls = {
        "approve": lambda: lending.approve_request(librarian, 999999),
        "reject": lambda: lending.reject_request(librarian, 999999, "Reason"),
        "cancel": lambda: lending.cancel_request(librarian, 999999),
        "issue": lambda: lending.issue_loan(librarian, 999999),
        "return": lambda: lending.return_loan(librarian, 999999),
    }
    assert_refused(conn, errors.NOT_FOUND, calls[action])
