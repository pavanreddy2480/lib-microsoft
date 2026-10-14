"""Contract tests for P3 availability logic; see docs/team/3.md."""
from datetime import date

import pytest

from lms.domain import clock
from lms.domain.errors import (
    BusinessRuleError, INVALID_DATES, PERIOD_TOO_LONG, START_IN_PAST,
)
from lms.domain.models import Copy, CopyStatus, Request, RequestStatus
from lms.services import availability as av

D = date
TODAY = D(2026, 8, 1)


class TestPureAvailability:
    @pytest.fixture(autouse=True)
    def fresh_db(self):
        """Override the seeded fixture: these functions do not require a DB."""
        clock.reset_business_today()
        yield
        clock.reset_business_today()

    @pytest.mark.parametrize("s1,e1,s2,e2,expected", [
        (1, 5, 3, 7, True),
        (1, 10, 3, 5, True),
        (3, 5, 1, 10, True),
        (2, 4, 2, 4, True),
        (1, 3, 3, 5, True),
        (1, 3, 4, 6, False),
        (4, 6, 1, 3, False),
        (3, 3, 3, 3, True),
    ])
    def test_inclusive_overlap(self, s1, e1, s2, e2, expected):
        assert av.overlaps(*(D(2026, 8, n) for n in (s1, e1, s2, e2))) is expected

    @pytest.mark.parametrize("start,end,code,message", [
        (None, TODAY, INVALID_DATES, "Please choose both a start and a return date."),
        (TODAY, None, INVALID_DATES, "Please choose both a start and a return date."),
        (None, None, INVALID_DATES, "Please choose both a start and a return date."),
        (D(2026, 8, 3), D(2026, 8, 2), INVALID_DATES,
         "Return date must be on or after the start date."),
        (D(2026, 7, 31), D(2026, 8, 2), START_IN_PAST,
         "Start date cannot be in the past (today is 01 Aug 2026)."),
        (TODAY, D(2026, 8, 31), PERIOD_TOO_LONG,
         "Borrowing period is 31 days; maximum is 30."),
    ])
    def test_invalid_period(self, start, end, code, message):
        with pytest.raises(BusinessRuleError) as caught:
            av.validate_period(start, end, TODAY)
        assert caught.value.code == code
        assert caught.value.message == message

    @pytest.mark.parametrize("start,end", [
        (TODAY, TODAY),
        (TODAY, D(2026, 8, 30)),
        (D(2026, 8, 5), D(2026, 8, 12)),
    ])
    def test_valid_period(self, start, end):
        assert av.validate_period(start, end, TODAY) is None

    @pytest.mark.parametrize("start,end,code", [
        (None, D(2026, 7, 1), INVALID_DATES),
        (D(2026, 7, 31), D(2026, 7, 30), INVALID_DATES),
        (D(2026, 7, 1), D(2026, 8, 31), START_IN_PAST),
    ])
    def test_validation_error_precedence(self, start, end, code):
        with pytest.raises(BusinessRuleError) as caught:
            av.validate_period(start, end, TODAY)
        assert caught.value.code == code

    @pytest.mark.parametrize("status,today,expected", [
        (RequestStatus.ISSUED, TODAY, D(2026, 8, 4)),
        (RequestStatus.ISSUED, D(2026, 8, 4), D(2026, 8, 4)),
        (RequestStatus.ISSUED, D(2026, 8, 10), D(2026, 8, 10)),
        *[(status, D(2026, 8, 10), D(2026, 8, 4))
          for status in RequestStatus if status != RequestStatus.ISSUED],
    ])
    def test_effective_end(self, status, today, expected):
        request = Request(
            id=1, member_id=1, title_id=1, copy_id=1,
            start_date=D(2026, 7, 21), end_date=D(2026, 8, 4),
            status=status, created_at="2026-07-21T00:00:00",
        )
        assert av.effective_end(request, today) == expected


@pytest.mark.parametrize("title,start,end,today,counts", [
    ("Clean Code", 2, 3, 1, (2, 4, 4)),
    ("Clean Code", 5, 6, 1, (4, 4, 4)),
    ("Introduction to Algorithms", 5, 7, 1, (2, 3, 3)),
    ("Design Patterns", 5, 7, 1, (1, 1, 2)),
    ("Artificial Intelligence: A Modern Approach", 6, 6, 1, (2, 3, 3)),
    ("Clean Code", 10, 11, 10, (2, 4, 4)),
])
def test_seeded_availability(conn, title_id, title, start, end, today, counts):
    clock.set_business_today(D(2026, 8, today))
    result = av.check_availability(conn, title_id(title), D(2026, 8, start), D(2026, 8, end))
    assert (result.free_count, result.total_in_service, result.total_copies) == counts
    assert result.available is (counts[0] > 0)


@pytest.mark.parametrize("status", [s for s in CopyStatus if s != CopyStatus.IN_SERVICE])
def test_out_of_service_copy_never_free(conn, status):
    copy = Copy(id=999, title_id=999, copy_code="TEST-1", status=status)
    assert av.is_copy_free(conn, copy, D(2026, 8, 5), D(2026, 8, 6), TODAY) is False


def test_free_copies_order_and_deterministic_selection(conn, title_id):
    tid = title_id("Clean Code")
    copies = av.free_copies(conn, tid, D(2026, 8, 2), D(2026, 8, 3))
    assert [copy.copy_code for copy in copies] == ["CC-3", "CC-4"]
    selected = av.find_free_copy(conn, tid, D(2026, 8, 2), D(2026, 8, 3))
    assert selected is not None
    assert selected.id == copies[0].id


def test_damaged_design_patterns_copy_excluded(conn, title_id):
    copies = av.free_copies(conn, title_id("Design Patterns"), D(2026, 8, 2), D(2026, 8, 3))
    assert [copy.copy_code for copy in copies] == ["DP-1"]


def test_catalog_contains_all_seeded_titles_with_consistent_counts(conn):
    start, end = D(2026, 8, 5), D(2026, 8, 7)
    catalog = av.catalog_availability(conn, start, end)
    assert {item.title.title for item in catalog} == {
        "Clean Code", "Introduction to Algorithms", "Design Patterns",
        "Database System Concepts", "Artificial Intelligence: A Modern Approach",
    }
    assert len(catalog) == 5
    for item in catalog:
        assert item.result == av.check_availability(conn, item.title.id, start, end)
