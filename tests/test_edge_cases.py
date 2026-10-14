from datetime import date
import sqlite3

import pytest

from lms.domain import clock, errors
from lms.domain.models import CopyStatus, RequestStatus
from lms.persistence import db, repository as repo
from lms.services import availability, lending

D = date
START, END = D(2026, 8, 5), D(2026, 8, 7)


def user(conn, name):
    return repo.get_user_by_username(conn, name)[0]


def copy_named(conn, code):
    return next(c for c in repo.list_copies(conn) if c.copy_code == code)


def snapshot(conn):
    return tuple(tuple(tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY id"))
                 for t in ("requests", "copies", "request_events"))


def refused(conn, code, action, text=None):
    before = snapshot(conn)
    with pytest.raises(errors.BusinessRuleError) as caught:
        action()
    assert caught.value.code == code
    if text:
        assert text in caught.value.message
    assert snapshot(conn) == before


def test_clean_code_capacity(conn, asha, ravi, title_id):
    tid = title_id("Clean Code")
    start, end = D(2026, 8, 2), D(2026, 8, 3)
    requests = [lending.submit_request(actor, tid, start, end) for actor in (asha, ravi)]
    assert len({r.copy_id for r in requests}) == 2
    assert availability.check_availability(conn, tid, start, end).free_count == 0
    refused(conn, errors.NO_COPY_AVAILABLE,
            lambda: lending.submit_request(user(conn, "meera"), tid, start, end), "already committed")


def test_design_patterns_capacity(conn, asha, ravi, title_id):
    tid = title_id("Design Patterns")
    request = lending.submit_request(asha, tid, START, END)
    assert repo.get_copy(conn, request.copy_id).copy_code == "DP-1"
    refused(conn, errors.NO_COPY_AVAILABLE, lambda: lending.submit_request(ravi, tid, START, END))


@pytest.mark.parametrize("state", ["pending", "reserved", "issued"])
def test_duplicate_active_request(conn, asha, librarian, title_id, state):
    tid = title_id("Database System Concepts")
    request = lending.submit_request(asha, tid, START, END)
    if state != "pending":
        lending.approve_request(librarian, request.id)
    if state == "issued":
        clock.set_business_today(START)
        lending.issue_loan(librarian, request.id)
    refused(conn, errors.DUPLICATE_REQUEST, lambda: lending.submit_request(asha, tid, START, END))


def test_nonoverlapping_request_allowed(asha, title_id):
    tid = title_id("Database System Concepts")
    lending.submit_request(asha, tid, START, END)
    assert lending.submit_request(asha, tid, D(2026, 8, 8), D(2026, 8, 9)).status == RequestStatus.PENDING


@pytest.mark.parametrize("state", ["reject", "cancel", "return"])
def test_terminal_request_allows_new_booking(asha, librarian, title_id, state):
    tid = title_id("Database System Concepts")
    request = lending.submit_request(asha, tid, START, END)
    if state == "reject":
        lending.reject_request(librarian, request.id, "Try again")
    elif state == "cancel":
        lending.cancel_request(asha, request.id)
    else:
        lending.approve_request(librarian, request.id)
        clock.set_business_today(START)
        lending.issue_loan(librarian, request.id)
        lending.return_loan(librarian, request.id)
    new = lending.submit_request(asha, tid, START, END)
    assert new.id != request.id
    assert new.status == RequestStatus.PENDING


@pytest.mark.parametrize("status", [RequestStatus.PENDING, RequestStatus.RESERVED, RequestStatus.ISSUED])
def test_database_trigger_blocks_direct_overlap(conn, asha, ravi, title_id, status):
    request = lending.submit_request(asha, title_id("Database System Concepts"), START, END)
    before = snapshot(conn)
    with pytest.raises(sqlite3.IntegrityError, match="COPY_OVERLAP"):
        repo.insert_request(conn, ravi.id, request.title_id, request.copy_id, END, D(2026, 8, 8), status)
    assert snapshot(conn) == before


def test_database_trigger_blocks_copy_reassignment(conn, asha, ravi, title_id):
    tid = title_id("Database System Concepts")
    first = lending.submit_request(asha, tid, START, END)
    second = lending.submit_request(ravi, tid, START, END)
    before = snapshot(conn)
    with pytest.raises(sqlite3.IntegrityError, match="COPY_OVERLAP"):
        repo.update_request_copy(conn, second.id, first.copy_id)
    assert snapshot(conn) == before


def test_damaged_return_moves_future_reservation(conn, asha, librarian, title_id):
    request = lending.submit_request(asha, title_id("Artificial Intelligence: A Modern Approach"), D(2026, 8, 10), D(2026, 8, 12))
    assert repo.get_copy(conn, request.copy_id).copy_code == "AIMA-1"
    lending.approve_request(librarian, request.id)
    loan = next(r for r in repo.list_requests(conn) if r.copy_id == request.copy_id and r.status == RequestStatus.ISSUED)
    assert loan.member_id == user(conn, "kiran").id
    clock.set_business_today(D(2026, 8, 3))
    returned, affected = lending.return_loan(librarian, loan.id, CopyStatus.DAMAGED)
    assert returned.status == RequestStatus.RETURNED
    moved = repo.get_request(conn, request.id)
    assert moved.status == RequestStatus.RESERVED
    assert moved.copy_id != request.copy_id
    assert repo.get_copy(conn, request.copy_id).status == CopyStatus.DAMAGED
    assert repo.get_copy(conn, moved.copy_id).status == CopyStatus.IN_SERVICE
    result = next(a for a in affected if a.request_id == request.id)
    assert result.outcome == "MOVED"
    assert (result.old_copy_id, result.new_copy_id) == (request.copy_id, moved.copy_id)
    assert "moved" in lending.get_request_history(request.id)[-1].note.lower()


@pytest.mark.parametrize("approved,expected", [(False, RequestStatus.REJECTED), (True, RequestStatus.CANCELLED)])
def test_unavailable_copy_closes_request_without_replacement(conn, asha, librarian, title_id, approved, expected):
    request = lending.submit_request(asha, title_id("Design Patterns"), START, END)
    if approved:
        lending.approve_request(librarian, request.id)
    affected = lending.set_copy_status(librarian, request.copy_id, CopyStatus.UNDER_REPAIR)
    stored = repo.get_request(conn, request.id)
    assert stored.status == expected
    assert "became unavailable" in stored.decision_note
    assert next(a for a in affected if a.request_id == request.id).outcome == "CLOSED"
    assert lending.get_request_history(request.id)[-1].to_status == expected.value


def test_inventory_change_preserves_issued_loan(conn, librarian):
    copy = copy_named(conn, "CC-1")
    loan = next(r for r in repo.list_requests(conn) if r.copy_id == copy.id and r.status == RequestStatus.ISSUED)
    lending.set_copy_status(librarian, copy.id, CopyStatus.LOST)
    assert repo.get_request(conn, loan.id).status == RequestStatus.ISSUED


def test_repair_restores_availability(conn, librarian, title_id):
    copy = copy_named(conn, "DP-2")
    lending.set_copy_status(librarian, copy.id, CopyStatus.IN_SERVICE)
    assert availability.check_availability(conn, title_id("Design Patterns"), START, END).free_count == 2


def test_overdue_copy_remains_unavailable(conn, title_id):
    clock.set_business_today(D(2026, 8, 10))
    start, end = D(2026, 8, 10), D(2026, 8, 11)
    copy = copy_named(conn, "CC-1")
    assert not availability.is_copy_free(conn, copy, start, end, clock.business_today())
    assert availability.check_availability(conn, title_id("Clean Code"), start, end).free_count == 2


@pytest.mark.parametrize("start,end,code", [
    (D(2026, 7, 31), D(2026, 8, 2), errors.START_IN_PAST),
    (D(2026, 8, 5), D(2026, 8, 4), errors.INVALID_DATES),
    (D(2026, 8, 1), D(2026, 8, 31), errors.PERIOD_TOO_LONG),
])
def test_invalid_submission_has_no_side_effects(conn, asha, title_id, start, end, code):
    refused(conn, code, lambda: lending.submit_request(asha, title_id("Database System Concepts"), start, end))


def test_thirty_day_submission_allowed(asha, title_id):
    assert lending.submit_request(asha, title_id("Database System Concepts"), D(2026, 8, 1), D(2026, 8, 30)).status == RequestStatus.PENDING


def test_no_partial_fulfillment_or_alternative_title(conn, asha, title_id):
    # Every DSC copy blocks one part of the interval; other titles remain free.
    tid = title_id("Database System Concepts")
    with db.transaction() as tx:
        for index, copy in enumerate(repo.list_copies(tx, tid)):
            start, end = (START, D(2026, 8, 6)) if index % 2 == 0 else (D(2026, 8, 7), D(2026, 8, 8))
            repo.insert_request(tx, user(tx, "meera").id, tid, copy.id, start, end, RequestStatus.RESERVED)
    refused(conn, errors.NO_COPY_AVAILABLE, lambda: lending.submit_request(asha, tid, START, D(2026, 8, 8)))


def test_all_out_of_service_explanation(conn, asha, librarian, title_id):
    tid = title_id("Design Patterns")
    lending.set_copy_status(librarian, copy_named(conn, "DP-1").id, CopyStatus.UNDER_REPAIR)
    result = availability.check_availability(conn, tid, START, END)
    assert (result.free_count, result.total_in_service, result.total_copies) == (0, 0, 2)
    assert result.reason == "No copies of 'Design Patterns' can be lent: all 2 copies are out of service (damaged / repair / lost / reference-only)."
    assert av_no_copy(conn, tid)
    refused(conn, errors.NO_COPY_AVAILABLE, lambda: lending.submit_request(asha, tid, START, END), "out of service")


def av_no_copy(conn, tid):
    return availability.free_copies(conn, tid, START, END) == [] and availability.find_free_copy(conn, tid, START, END) is None


def test_submit_rolls_back_if_audit_write_fails(conn, asha, title_id, monkeypatch):
    tid = title_id("Database System Concepts")
    before = snapshot(conn)
    def fail_event(*args, **kwargs):
        raise RuntimeError("simulated audit failure")
    monkeypatch.setattr(repo, "insert_event", fail_event)
    with pytest.raises(RuntimeError, match="simulated audit failure"):
        lending.submit_request(asha, tid, START, END)
    assert snapshot(conn) == before
