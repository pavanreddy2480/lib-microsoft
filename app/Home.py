"""Home / login page.  OWNER: Person 1 (see docs/team/1.md).

Run from the project root:  python -m streamlit run app/Home.py

Not logged in -> login form (auth.login) + demo credentials.
Logged in     -> sidebar, role-specific list of pages, lifecycle diagram (PRD §1).
"""
import streamlit as st

from lms.domain.errors import BusinessRuleError
from lms.domain.models import Role
from lms.persistence import seed
from lms.services import auth
from lms.ui.common import current_user, sidebar

st.set_page_config(page_title="Library Management System", layout="wide")
seed.ensure_db()

LIFECYCLE = """\
PENDING ──approve──▶ RESERVED ──issue──▶ ISSUED ──return──▶ RETURNED
   │                    │
   ├──reject──▶ REJECTED └──cancel──▶ CANCELLED
   └──cancel (member withdraw)──▶ CANCELLED

Active (holds a copy):     PENDING · RESERVED · ISSUED
Terminal (copy released):  REJECTED · CANCELLED · RETURNED"""

PAGES = {
    Role.MEMBER: [
        ("Catalog", "check availability for your dates and submit a request"),
        ("My Requests", "track status and history, cancel a PENDING or RESERVED request"),
    ],
    Role.LIBRARIAN: [
        ("Review Queue", "approve or reject PENDING requests (a reason is required to reject)"),
        ("Loans", "issue confirmed reservations and take returns, recording the copy's condition"),
        ("Inventory", "change a copy's status and reset the demo data"),
    ],
}

st.title("Library Management System")
user = current_user()

if user is None:
    st.caption("Request → review → confirmed reservation → loan → return, with copy-level availability.")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        try:
            st.session_state["user"] = auth.login(username.strip(), password)
        except BusinessRuleError as err:
            st.error(err.message)
        else:
            st.rerun()
    st.info(
        "**Demo credentials**  \n"
        "Librarian: `librarian` / `lib123`  \n"
        "Members: `asha`, `ravi`, `meera`, `kiran` / `pass123`"
    )
else:
    sidebar()
    st.subheader(f"Welcome, {user.full_name}")
    st.write(f"You are logged in as a **{user.role.value}**. Use the sidebar to open a page:")
    st.markdown("\n".join(f"- **{name}**: {what}" for name, what in PAGES[user.role]))
    st.markdown("#### Request lifecycle")
    st.code(LIFECYCLE, language=None)
