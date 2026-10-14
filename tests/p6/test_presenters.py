"""Unit tests: pure presentation logic (no Streamlit, no DB)."""
from datetime import date

import pytest

from lms.domain.models import Event, Request, RequestStatus
from lms.ui.librarian import presenters
from lms.ui.librarian.views import AffectedRow, RequestRow

D = date


def row(id=1, status=RequestStatus.PENDING, end=D(2026, 8, 8), start=D(2026, 8, 4), **kw):
    base = dict(member_name="Asha Rao", title="Clean Code", copy_code="CC-3",
                created_at="2026-07-30 10:00:00")
    base.update(kw)
    return RequestRow(id=id, start_date=start, end_date=end, status=status, **base)


def test_oldest_first_orders_by_id_ascending():
    rows = [row(3), row(1), row(2)]
    assert [r.id for r in presenters.oldest_first(rows)] == [1, 2, 3]


@pytest.mark.parametrize("status,today,expected", [
    (RequestStatus.ISSUED, D(2026, 8, 9), True),    # due 8 Aug, still out on 9 Aug
    (RequestStatus.ISSUED, D(2026, 8, 8), False),   # due date itself is not overdue (inclusive)
    (RequestStatus.RESERVED, D(2026, 8, 20), False),  # only loans can be overdue
    (RequestStatus.RETURNED, D(2026, 8, 20), False),
])
def test_is_overdue(status, today, expected):
    assert presenters.is_overdue(row(status=status), today) is expected


def test_only_and_filter_by_status():
    rows = [row(1, RequestStatus.PENDING), row(2, RequestStatus.ISSUED), row(3, RequestStatus.RETURNED)]
    assert [r.id for r in presenters.only(rows, RequestStatus.ISSUED)] == [2]
    got = presenters.filter_by_status(rows, [RequestStatus.PENDING, RequestStatus.RETURNED])
    assert [r.id for r in got] == [1, 3]
    assert presenters.filter_by_status(rows, []) == []


def test_period_and_details_text():
    r = row(5, copy_code="DP-1", title="Design Patterns")
    assert presenters.fmt_period(D(2026, 8, 4), D(2026, 8, 8)) == "04 Aug 2026 → 08 Aug 2026"
    assert presenters.request_headline(r) == "#5 · Design Patterns"
    details = presenters.request_details(r)
    assert "Asha Rao" in details and "DP-1" in details and "04 Aug 2026 → 08 Aug 2026" in details


def test_requests_table_newest_first_and_overdue_label():
    rows = [row(1, RequestStatus.ISSUED, end=D(2026, 8, 4)), row(2, RequestStatus.PENDING)]
    table = presenters.requests_table(rows, today=D(2026, 8, 10))
    assert [t["ID"] for t in table] == [2, 1]
    assert table[1]["Status"] == "OVERDUE"
    assert table[0]["Status"] == "PENDING"


def test_outcome_severity_strategy_table():
    assert presenters.outcome_severity(AffectedRow(1, "MOVED", "m")) == "info"
    assert presenters.outcome_severity(AffectedRow(1, "CLOSED", "c")) == "warning"
    assert presenters.outcome_severity(AffectedRow(1, "SOMETHING_NEW", "x")) == "warning"  # safe default


def test_affected_text():
    assert presenters.affected_text(AffectedRow(7, "MOVED", "moved from A to B")) == \
        "Request #7 MOVED: moved from A to B"


def _req(id, status, start, end, member_id=1):
    return Request(id=id, member_id=member_id, title_id=1, copy_id=1, start_date=start,
                   end_date=end, status=status, created_at="x")


def test_describe_commitment_picks_earliest_and_handles_none():
    assert presenters.describe_commitment([], lambda r: "x") == ""
    later = _req(2, RequestStatus.PENDING, D(2026, 8, 10), D(2026, 8, 12))
    earlier = _req(3, RequestStatus.RESERVED, D(2026, 8, 4), D(2026, 8, 8))
    text = presenters.describe_commitment([later, earlier], lambda r: "Meera")
    assert text == "RESERVED 04 Aug 2026 → 08 Aug 2026 (Meera)"


def test_history_table_maps_events_and_blank_from_status():
    events = [Event(1, 9, None, "PENDING", "asha", "", "t1"),
              Event(2, 9, "PENDING", "RESERVED", "librarian", "ok", "t2")]
    table = presenters.history_table(events)
    assert table[0]["From"] == "-" and table[0]["To"] == "PENDING"
    assert table[1] == {"At": "t2", "From": "PENDING", "To": "RESERVED", "By": "librarian", "Note": "ok"}
