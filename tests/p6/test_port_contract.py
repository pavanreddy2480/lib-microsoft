"""Integration/contract tests for LibrarianPort.

The same assertions run against (a) the in-memory fake and (b) the real adapter over the
real services + SQLite. The real variant skips itself until P2/P3/P4 are merged
(their functions still raise NotImplementedError) and then starts running unchanged,
which is also what keeps the fake honest.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest

from lms.domain import clock
from lms.domain.errors import (
    INVALID_TRANSITION, ISSUE_NOT_ALLOWED, NOT_AUTHORIZED, REASON_REQUIRED, BusinessRuleError,
)
from lms.domain.models import CopyStatus, RequestStatus, Role, User
from lms.ui.librarian.port import LibrarianPort

from .fakes import InMemoryPort

D = date


@dataclass
class Env:
    port: LibrarianPort
    librarian: User
    member: User
    pending_id: int      # a PENDING request
    reserved_id: int     # a RESERVED request starting after 2026-08-01
    issued_id: int       # an ISSUED loan on CC-1


def _status_of(port, request_id):
    return next(r.status for r in port.requests() if r.id == request_id)


def _first(port, status, copy_code=None):
    return next(r.id for r in reversed(port.requests([status]))
                if copy_code is None or r.copy_code == copy_code)


def _fake_env():
    port = InMemoryPort()
    lib = User(1, "librarian", "Library Staff", Role.LIBRARIAN)
    mem = User(2, "asha", "Asha Rao", Role.MEMBER)
    return Env(port, lib, mem, _first(port, RequestStatus.PENDING),
               _first(port, RequestStatus.RESERVED, "ITA-1"),
               _first(port, RequestStatus.ISSUED, "CC-1"))


def _real_env(tmp_path):
    from lms.persistence import db, seed
    from lms.persistence import repository as repo
    from lms.services import lending
    from lms.ui.librarian.service_port import ServicePort

    db.set_db_path(tmp_path / "contract.db")
    clock.reset_business_today()
    try:
        seed.reset_db()
        conn = db.get_conn()
        try:
            lib, _ = repo.get_user_by_username(conn, "librarian")
            asha, _ = repo.get_user_by_username(conn, "asha")
            dsc = next(t.id for t in repo.list_titles(conn) if t.title == "Database System Concepts")
        finally:
            conn.close()
        lending.submit_request(asha, dsc, D(2026, 8, 5), D(2026, 8, 12))
    except NotImplementedError:
        pytest.skip("services/persistence not implemented yet (P2/P3/P4)")
    port = ServicePort()
    return Env(port, lib, asha, _first(port, RequestStatus.PENDING),
               _first(port, RequestStatus.RESERVED, "ITA-1"),
               _first(port, RequestStatus.ISSUED, "CC-1"))


@pytest.fixture(params=["fake", "real"])
def env(request, tmp_path) -> Env:
    return _fake_env() if request.param == "fake" else _real_env(tmp_path)


# ---------------- review (BR6, BR7) ----------------
def test_approve_moves_pending_to_reserved(env):
    result = env.port.approve(env.librarian, env.pending_id, "ok")
    assert result.status is RequestStatus.RESERVED
    assert _status_of(env.port, env.pending_id) is RequestStatus.RESERVED


def test_reject_requires_a_reason_and_changes_nothing(env):
    with pytest.raises(BusinessRuleError) as err:
        env.port.reject(env.librarian, env.pending_id, "   ")
    assert err.value.code == REASON_REQUIRED
    assert _status_of(env.port, env.pending_id) is RequestStatus.PENDING


def test_reject_is_terminal_and_cannot_be_approved(env):
    env.port.reject(env.librarian, env.pending_id, "Out of quota")
    assert _status_of(env.port, env.pending_id) is RequestStatus.REJECTED
    with pytest.raises(BusinessRuleError) as err:
        env.port.approve(env.librarian, env.pending_id)
    assert err.value.code == INVALID_TRANSITION


def test_a_member_cannot_review(env):
    with pytest.raises(BusinessRuleError) as err:
        env.port.approve(env.member, env.pending_id)
    assert err.value.code == NOT_AUTHORIZED


# ---------------- reservations / loans (BR8, BR9) ----------------
def test_issue_before_start_date_is_refused(env):
    with pytest.raises(BusinessRuleError) as err:
        env.port.issue(env.librarian, env.reserved_id)  # ITA-1 starts 4 Aug, today 1 Aug
    assert err.value.code == ISSUE_NOT_ALLOWED


def test_issue_succeeds_once_the_business_date_reaches_the_start(env):
    clock.set_business_today(D(2026, 8, 4))
    assert env.port.issue(env.librarian, env.reserved_id).status is RequestStatus.ISSUED


def test_cancel_reservation_closes_it(env):
    assert env.port.cancel(env.librarian, env.reserved_id, "changed plans").status \
        is RequestStatus.CANCELLED


def test_issued_loan_cannot_be_cancelled(env):
    with pytest.raises(BusinessRuleError) as err:
        env.port.cancel(env.librarian, env.issued_id)
    assert err.value.code == INVALID_TRANSITION


def test_return_in_service_releases_the_copy(env):
    outcome = env.port.return_loan(env.librarian, env.issued_id, CopyStatus.IN_SERVICE, "fine")
    assert outcome.request.status is RequestStatus.RETURNED
    assert outcome.affected == ()
    cc1 = next(c for c in env.port.inventory() if c.copy_code == "CC-1")
    assert cc1.status is CopyStatus.IN_SERVICE and cc1.commitment == ""


def test_return_damaged_takes_the_copy_out_of_service(env):
    outcome = env.port.return_loan(env.librarian, env.issued_id, CopyStatus.DAMAGED, "water damage")
    assert outcome.request.status is RequestStatus.RETURNED
    cc1 = next(c for c in env.port.inventory() if c.copy_code == "CC-1")
    assert cc1.status is CopyStatus.DAMAGED


# ---------------- inventory (BR5) ----------------
def test_inventory_lists_every_copy_with_seeded_state(env):
    copies = {c.copy_code: c for c in env.port.inventory()}
    assert len(copies) == 17
    assert copies["DP-2"].status is CopyStatus.DAMAGED
    assert copies["CC-1"].commitment.startswith("ISSUED")


def test_set_copy_status_roundtrip(env):
    dp1 = next(c for c in env.port.inventory() if c.copy_code == "DP-1")
    env.port.set_copy_status(env.librarian, dp1.id, CopyStatus.UNDER_REPAIR, "spine")
    assert next(c for c in env.port.inventory() if c.copy_code == "DP-1").status \
        is CopyStatus.UNDER_REPAIR
    env.port.set_copy_status(env.librarian, dp1.id, CopyStatus.IN_SERVICE, "fixed")
    assert next(c for c in env.port.inventory() if c.copy_code == "DP-1").status \
        is CopyStatus.IN_SERVICE


def test_history_records_the_approval(env):
    env.port.approve(env.librarian, env.pending_id, "ok")
    assert [e.to_status for e in env.port.history(env.pending_id)][-1] == "RESERVED"
