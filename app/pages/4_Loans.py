"""Reservations -> issue, loans -> return (LIBRARIAN).  OWNER: Person 6 (see docs/team/6.md).

A return releases the copy unless the librarian marks it unavailable (BR9); marking it
unavailable also reports every future commitment that had to move or close (BR5).
"""
import streamlit as st

from lms.domain.models import CopyStatus, RequestStatus, Role
from lms.ui.common import fmt_date, page_setup
from lms.ui.librarian import presenters
from lms.ui.librarian.components import act, flash, flash_affected, show_flash
from lms.ui.librarian.registry import get_port

user = page_setup("Loans", Role.LIBRARIAN)
port = get_port()
show_flash()
today = port.today()
rows = port.requests()

tab_res, tab_loans, tab_all = st.tabs(["Confirmed reservations", "Active loans", "All requests"])

with tab_res:
    reservations = presenters.oldest_first(presenters.only(rows, RequestStatus.RESERVED))
    if not reservations:
        st.info("No confirmed reservations.")
    for row in reservations:
        with st.container(border=True):
            left, right = st.columns([3, 2])
            left.markdown(f"**{presenters.request_headline(row)}**")
            left.caption(presenters.request_details(row))
            note = right.text_input("Cancellation note (optional)", key=f"cancel_note_{row.id}")
            issue_col, cancel_col = right.columns(2)
            if issue_col.button("Issue", key=f"issue_{row.id}", type="primary"):
                act(port.issue, user, row.id,
                    success=f"Request #{row.id} issued - {row.copy_code} is on loan.")
            if cancel_col.button("Cancel", key=f"cancel_{row.id}"):
                act(port.cancel, user, row.id, note,
                    success=f"Reservation #{row.id} cancelled - {row.copy_code} is free again.")

with tab_loans:
    loans = presenters.oldest_first(presenters.only(rows, RequestStatus.ISSUED))
    if not loans:
        st.info("No active loans.")
    for row in loans:
        with st.container(border=True):
            left, right = st.columns([3, 2])
            badge = "  :red[**OVERDUE**]" if presenters.is_overdue(row, today) else ""
            left.markdown(f"**{presenters.request_headline(row)}**{badge}")
            left.caption(presenters.request_details(row))
            condition = right.selectbox(
                "Condition on return", list(CopyStatus), format_func=lambda s: s.value,
                key=f"condition_{row.id}")
            note = right.text_input("Return note", key=f"return_note_{row.id}")

            def _after_return(outcome, request_id=row.id, copy_code=row.copy_code):
                flash("success", f"Request #{request_id} returned - condition recorded for {copy_code}.")
                flash_affected(outcome.affected)

            if right.button("Return", key=f"return_{row.id}", type="primary"):
                act(port.return_loan, user, row.id, condition, note, success=_after_return)

with tab_all:
    chosen = st.multiselect("Status", list(RequestStatus), default=list(RequestStatus),
                            format_func=lambda s: s.value, key="all_status_filter")
    shown = presenters.filter_by_status(rows, chosen)
    st.dataframe(presenters.requests_table(shown, today), hide_index=True)
    if shown:
        picked = st.selectbox("Show history for request", [r.id for r in shown],
                              key="history_pick")
        with st.expander(f"History of request #{picked}"):
            st.dataframe(presenters.history_table(port.history(picked)),
                         hide_index=True)
