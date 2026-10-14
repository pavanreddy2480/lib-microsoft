"""Tests of the fake's reallocation policy (CONTEXT.md §3: auto-move, else close).

Only the fake is covered here; the real policy belongs to P4's `_handle_copy_out_of_service`
and is exercised by P7's lifecycle tests. This pins the behaviour the UI e2e tests rely on.
"""

from lms.domain.models import CopyStatus, RequestStatus



def _row(port, request_id):
    return next(r for r in port.requests() if r.id == request_id)


def test_damaged_return_moves_future_reservation_to_a_free_copy(fake_port, librarian_user):
    issued = next(r for r in fake_port.requests([RequestStatus.ISSUED]) if r.copy_code == "AIMA-1")
    future = next(r for r in fake_port.requests([RequestStatus.RESERVED])
                  if r.copy_code == "AIMA-1")  # asha, 10-12 Aug
    outcome = fake_port.return_loan(librarian_user, issued.id, CopyStatus.DAMAGED, "torn")
    assert [(a.request_id, a.outcome) for a in outcome.affected] == [(future.id, "MOVED")]
    assert _row(fake_port, future.id).copy_code != "AIMA-1"
    assert _row(fake_port, future.id).status is RequestStatus.RESERVED


def test_out_of_service_closes_when_no_other_copy_is_free(fake_port, librarian_user):
    # Design Patterns: DP-2 already damaged, so DP-1 is the only lendable copy.
    pending = next(r for r in fake_port.requests([RequestStatus.PENDING]) if r.copy_code == "DP-1")
    dp1 = next(c for c in fake_port.inventory() if c.copy_code == "DP-1")
    affected = fake_port.set_copy_status(librarian_user, dp1.id, CopyStatus.UNDER_REPAIR, "spine")
    assert [(a.request_id, a.outcome) for a in affected] == [(pending.id, "CLOSED")]
    closed = _row(fake_port, pending.id)
    assert closed.status is RequestStatus.REJECTED
    assert "became unavailable" in closed.decision_note
