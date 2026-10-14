"""Inventory / copy status (LIBRARIAN).  OWNER: Person 6 (see docs/team/6.md).

Only IN_SERVICE copies can be allocated (BR5). Changing a copy's status reports every
PENDING/RESERVED commitment that was moved to another copy or closed.
"""
import streamlit as st

from lms.domain.models import CopyStatus, Role
from lms.ui.common import page_setup
from lms.ui.librarian.components import act, flash_affected, show_flash
from lms.ui.librarian.registry import get_port

user = page_setup("Inventory", Role.LIBRARIAN)
port = get_port()
show_flash()
copies = port.inventory()

st.dataframe(
    [{"Title": c.title, "Copy": c.copy_code, "Status": c.status.value, "Note": c.note,
      "Next commitment": c.commitment or "-"} for c in copies],
    hide_index=True,
)

st.subheader("Change copy status")
with st.form("change_status"):
    copy = st.selectbox("Copy", copies, format_func=lambda c: f"{c.copy_code} · {c.title}",
                        key="inv_copy")
    status = st.selectbox("New status", list(CopyStatus), format_func=lambda s: s.value,
                          key="inv_status")
    note = st.text_input("Note", key="inv_note")
    submitted = st.form_submit_button("Apply")

if submitted and copy is not None:
    def _after(affected, code=copy.copy_code, new=status):
        from lms.ui.librarian.components import flash
        flash("success", f"{code} is now {new.value}.")
        flash_affected(affected)

    act(port.set_copy_status, user, copy.id, status, note, success=_after)

st.subheader("Demo tools")
confirmed = st.checkbox("I understand this deletes all data", key="reset_confirm")
if st.button("Reset demo data", disabled=not confirmed, key="reset_button"):
    port.reset_demo()
    st.rerun()
