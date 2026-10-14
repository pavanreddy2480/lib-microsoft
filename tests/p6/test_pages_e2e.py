"""End-to-end tests: the real Streamlit page scripts run headless via AppTest.

Each test drives the actual page file (widgets, buttons, reruns, flash messages) against
the in-memory port, so the full UI path page -> components -> presenters -> port is
exercised without a database.
"""
from __future__ import annotations

from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from lms.domain import clock
from lms.domain.models import CopyStatus, RequestStatus

from .conftest import PAGES

D = date


def run_page(name: str, user=None) -> AppTest:
    at = AppTest.from_file(str(PAGES / name), default_timeout=15)
    if user is not None:
        at.session_state["user"] = user
    return at.run()


def texts(elements) -> str:
    return " | ".join(e.value for e in elements)


# ---------------- access control ----------------
def test_anonymous_visitor_is_told_to_log_in(fake_port):
    at = run_page("3_Review_Queue.py")
    assert "log in" in texts(at.warning).lower()
    assert len(at.button) == 0


@pytest.mark.parametrize("page", ["3_Review_Queue.py", "4_Loans.py", "5_Inventory.py"])
def test_members_cannot_open_librarian_pages(fake_port, member_user, page):
    at = run_page(page, member_user)
    assert "librarians only" in texts(at.error)
    assert fake_port.calls == []


# ---------------- review queue ----------------
def test_queue_lists_pending_requests_oldest_first(fake_port, librarian_user):
    at = run_page("3_Review_Queue.py", librarian_user)
    assert not at.exception
    headlines = [m.value for m in at.markdown if m.value.startswith("**#")]
    assert headlines == ["**#1 · Database System Concepts**", "**#2 · Design Patterns**"]
    assert "Asha Rao" in texts(at.caption)


def test_approve_flow_shows_confirmation_and_removes_the_row(fake_port, librarian_user):
    at = run_page("3_Review_Queue.py", librarian_user)
    at.text_input(key="note_1").set_value("looks fine").run()
    at.button(key="approve_1").click().run()
    assert ("approve", 1, "looks fine") in fake_port.calls
    assert "Request #1 approved" in texts(at.success)
    assert [r.id for r in fake_port.requests([RequestStatus.RESERVED]) if r.id == 1] == [1]
    assert not any(b.key == "approve_1" for b in at.button)  # no longer pending


def test_reject_without_reason_shows_the_rule_error_and_keeps_the_request(fake_port, librarian_user):
    at = run_page("3_Review_Queue.py", librarian_user)
    at.button(key="reject_1").click().run()
    assert "A rejection reason is required." in texts(at.error)
    assert any(b.key == "reject_1" for b in at.button)
    assert fake_port.requests([RequestStatus.REJECTED]) == []


def test_reject_with_reason_releases_the_request(fake_port, librarian_user):
    at = run_page("3_Review_Queue.py", librarian_user)
    at.text_input(key="reason_2").set_value("Quota exceeded").run()
    at.button(key="reject_2").click().run()
    assert "Request #2 rejected" in texts(at.success)
    rejected = fake_port.requests([RequestStatus.REJECTED])
    assert [r.id for r in rejected] == [2] and rejected[0].decision_note == "Quota exceeded"


def test_empty_queue_message(fake_port, librarian_user):
    for rid in (1, 2):
        fake_port.reject(librarian_user, rid, "no")
    at = run_page("3_Review_Queue.py", librarian_user)
    assert "No requests awaiting review." in texts(at.info)


# ---------------- loans ----------------
def test_issue_before_start_shows_a_clear_error(fake_port, librarian_user):
    at = run_page("4_Loans.py", librarian_user)
    at.button(key="issue_3").click().run()  # ITA-1 starts 04 Aug, today is 01 Aug
    assert "Cannot issue before the start date (04 Aug 2026)." in texts(at.error)
    assert fake_port.requests([RequestStatus.ISSUED]).__len__() == 2  # unchanged


def test_issue_works_after_moving_the_business_date(fake_port, librarian_user):
    clock.set_business_today(D(2026, 8, 4))
    at = run_page("4_Loans.py", librarian_user)
    at.button(key="issue_3").click().run()
    assert "Request #3 issued" in texts(at.success)
    assert next(r for r in fake_port.requests() if r.id == 3).status is RequestStatus.ISSUED


def test_cancel_reservation_releases_it(fake_port, librarian_user):
    at = run_page("4_Loans.py", librarian_user)
    at.button(key="cancel_3").click().run()
    assert "Reservation #3 cancelled" in texts(at.success)
    assert next(r for r in fake_port.requests() if r.id == 3).status is RequestStatus.CANCELLED


def test_overdue_loans_get_a_badge_only_when_past_due(fake_port, librarian_user):
    at = run_page("4_Loans.py", librarian_user)
    assert not any("OVERDUE" in m.value for m in at.markdown)  # today 01 Aug, due 04 Aug
    clock.set_business_today(D(2026, 8, 10))
    at = run_page("4_Loans.py", librarian_user)
    assert sum("OVERDUE" in m.value for m in at.markdown) == 2  # CC-1 and AIMA-1


def test_return_in_service_confirms_without_warnings(fake_port, librarian_user):
    at = run_page("4_Loans.py", librarian_user)
    at.button(key="return_5").click().run()
    assert "Request #5 returned" in texts(at.success)
    assert len(at.warning) == 0 and len(at.info) == 0


def test_return_damaged_reports_the_moved_reservation(fake_port, librarian_user):
    at = run_page("4_Loans.py", librarian_user)
    at.selectbox(key="condition_6").set_value(CopyStatus.DAMAGED).run()
    at.button(key="return_6").click().run()
    assert "Request #6 returned" in texts(at.success)
    assert "Request #7 MOVED" in texts(at.info)
    assert next(c for c in fake_port.inventory() if c.copy_code == "AIMA-1").status is CopyStatus.DAMAGED


def test_all_requests_tab_filters_and_shows_history(fake_port, librarian_user):
    fake_port.approve(librarian_user, 1, "ok")
    at = run_page("4_Loans.py", librarian_user)
    assert len(at.dataframe) >= 1
    at.multiselect(key="all_status_filter").set_value([RequestStatus.PENDING]).run()
    assert set(at.dataframe[0].value["Status"]) == {"PENDING"}
    at.multiselect(key="all_status_filter").set_value([RequestStatus.RESERVED]).run()
    at.selectbox(key="history_pick").set_value(1).run()
    assert at.dataframe[-1].value["To"].tolist() == ["RESERVED"]


# ---------------- inventory ----------------
def test_inventory_table_lists_all_copies(fake_port, librarian_user):
    at = run_page("5_Inventory.py", librarian_user)
    table = next(m.value for m in at.markdown if 'class="lms-table"' in m.value)
    rows = table.split("<tbody>")[1].split("<tr>")[1:]
    assert len(rows) == 17
    dp2 = next(r for r in rows if "<code>DP-2</code>" in r)
    assert "Damaged" in dp2


def test_marking_the_only_lendable_copy_unavailable_closes_its_request(fake_port, librarian_user):
    at = run_page("5_Inventory.py", librarian_user)
    index = next(i for i, c in enumerate(fake_port.inventory()) if c.copy_code == "DP-1")
    at.selectbox(key="inv_copy").select_index(index)
    at.selectbox(key="inv_status").select(CopyStatus.UNDER_REPAIR)
    at.text_input(key="inv_note").set_value("spine")
    at.button[0].click().run()  # form submit button "Apply"
    assert "DP-1 is now UNDER_REPAIR." in texts(at.success)
    assert "Request #2 CLOSED" in texts(at.warning)
    assert next(c for c in fake_port.inventory() if c.copy_code == "DP-1").status \
        is CopyStatus.UNDER_REPAIR


def test_restoring_a_copy_to_service(fake_port, librarian_user):
    fake_port.set_copy_status(librarian_user, 14, CopyStatus.UNDER_REPAIR, "")
    at = run_page("5_Inventory.py", librarian_user)
    at.selectbox(key="inv_copy").select_index(13)  # id 14
    at.selectbox(key="inv_status").select(CopyStatus.IN_SERVICE)
    at.button[0].click().run()
    assert next(c for c in fake_port.inventory() if c.id == 14).status is CopyStatus.IN_SERVICE


def test_reset_needs_the_confirmation_checkbox(fake_port, librarian_user):
    at = run_page("5_Inventory.py", librarian_user)
    reset = at.button(key="reset_button")
    assert reset.disabled
    at.checkbox(key="reset_confirm").check().run()
    at.button(key="reset_button").click().run()
    assert fake_port.reset_count == 1
