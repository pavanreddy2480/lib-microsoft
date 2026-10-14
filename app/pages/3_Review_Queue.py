"""Review queue (LIBRARIAN).  OWNER: Person 6 (see docs/team/6.md).

Every PENDING request waits here for a decision (BR6): approve -> RESERVED,
or reject with a mandatory reason -> REJECTED (the copy is released, BR7).
"""
import streamlit as st

from lms.domain.models import RequestStatus, Role
from lms.ui.common import page_setup
from lms.ui.librarian import presenters
from lms.ui.librarian.components import act, show_flash
from lms.ui.librarian.registry import get_port

user = page_setup("Review Queue", Role.LIBRARIAN)
port = get_port()
show_flash()

pending = presenters.oldest_first(port.requests([RequestStatus.PENDING]))
st.caption(f"{len(pending)} request(s) awaiting review, oldest first.")

if not pending:
    st.info("No requests awaiting review.")

for row in pending:
    with st.container(border=True):
        left, right = st.columns([3, 2])
        left.markdown(f"**{presenters.request_headline(row)}**")
        left.caption(presenters.request_details(row))

        note = right.text_input("Approval note (optional)", key=f"note_{row.id}")
        reason = right.text_input("Rejection reason (required)", key=f"reason_{row.id}")
        approve_col, reject_col = right.columns(2)
        if approve_col.button("Approve", key=f"approve_{row.id}", type="primary"):
            act(port.approve, user, row.id, note,
                success=f"Request #{row.id} approved - now RESERVED on {row.copy_code}.")
        if reject_col.button("Reject", key=f"reject_{row.id}"):
            act(port.reject, user, row.id, reason,
                success=f"Request #{row.id} rejected - {row.copy_code} is free again.")
