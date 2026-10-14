"""My requests (MEMBER).  OWNER: Person 5 (see docs/team/5.md).

Active requests (PENDING / RESERVED / ISSUED) with a Cancel button where the
rules allow it (BR8), and the closed history with decision notes (BR7, BR10).
Rejected requests can't be edited; the member creates a new one instead.
"""
from contextlib import closing

import streamlit as st

from lms.domain import clock
from lms.domain.models import ACTIVE_STATUSES, RequestStatus, Role
from lms.persistence import db
from lms.persistence import repository as repo
from lms.services import lending
from lms.ui.common import fmt_date, page_setup, run_action, status_badge

user = page_setup("My Requests", Role.MEMBER)
today = clock.business_today()

for message in st.session_state.pop("member_flash", []):
    st.success(message)

with closing(db.get_conn()) as conn:
    requests = repo.list_requests(conn, member_id=user.id)
    titles = {t.id: t.title for t in repo.list_titles(conn)}
    copies = {c.id: c.copy_code for c in repo.list_copies(conn)}

active = [r for r in requests if r.status in ACTIVE_STATUSES]
closed = [r for r in requests if r.status not in ACTIVE_STATUSES]

HINT = {
    RequestStatus.PENDING: "Awaiting librarian review. Your copy is held.",
    RequestStatus.RESERVED: "Confirmed. Collect it from the library on or after the start date.",
    RequestStatus.ISSUED: "On loan. Please return it by the return date.",
}


def request_card(r, cancellable: bool) -> None:
    with st.container(border=True):
        info, action = st.columns([4, 1])
        overdue = r.status == RequestStatus.ISSUED and r.end_date < today
        badges = status_badge(r.status) + (" " + status_badge("OVERDUE") if overdue else "")
        info.markdown(f"**#{r.id} · {titles.get(r.title_id, '?')}** {badges}")
        info.caption(f"Copy `{copies.get(r.copy_id, '?')}` · "
                     f"{fmt_date(r.start_date)} → {fmt_date(r.end_date)}")
        if r.status in HINT:
            info.write(HINT[r.status])
        if r.decision_note:
            info.caption(f"Note: {r.decision_note}")
        if r.status == RequestStatus.REJECTED:
            info.caption("Rejected requests can't be edited. "
                         "Create a new request from the Catalog.")
        if cancellable and action.button("Cancel", key=f"cancel_{r.id}", width="stretch"):
            if run_action(lending.cancel_request, user, r.id) is not None:
                st.session_state.setdefault("member_flash", []).append(
                    f"Request #{r.id} cancelled. The copy is free for others again.")
                st.rerun()
        with info.expander("History"):
            st.dataframe(
                [{"At": e.at, "From": e.from_status or "-", "To": e.to_status,
                  "By": e.actor, "Note": e.note}
                 for e in lending.get_request_history(r.id)],
                hide_index=True, width="stretch",
            )


tab_active, tab_closed = st.tabs([f"Active ({len(active)})", f"History ({len(closed)})"])
with tab_active:
    if not active:
        st.info("No active requests. Find a book on the **Catalog** page.")
    for r in active:
        request_card(r, cancellable=r.status in (RequestStatus.PENDING, RequestStatus.RESERVED))
with tab_closed:
    if not closed:
        st.info("Nothing here yet.")
    for r in closed:
        request_card(r, cancellable=False)
