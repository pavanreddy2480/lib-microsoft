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
from contextlib import closing

from lms.domain import clock
from lms.domain.models import RequestStatus
from lms.persistence import db
from lms.persistence import repository as repo
from lms.ui.common import apply_style, current_user, sidebar

st.set_page_config(page_title="Library Management System", page_icon="📚", layout="wide")
apply_style()
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

user = current_user()

if user is None:
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.title("📚 Library")
        st.caption("Request → review → reservation → loan → return, "
                   "with copy-level availability.")
        with st.form("login", border=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary")
        if submitted:
            try:
                st.session_state["user"] = auth.login(username.strip(), password)
            except BusinessRuleError as err:
                st.error(err.message)
            else:
                st.rerun()
        with st.expander("Demo credentials"):
            st.markdown("Librarian: `librarian` / `lib123`  \n"
                        "Members: `asha`, `ravi`, `meera`, `kiran` / `pass123`")
else:
    sidebar()
    today = clock.business_today()
    st.title(f"Welcome, {user.full_name}")
    st.caption(f"{user.role.value.title()} · business date {today:%d %b %Y}")

    with closing(db.get_conn()) as conn:
        member_id = None if user.role == Role.LIBRARIAN else user.id
        reqs = repo.list_requests(conn, member_id=member_id)
    count = lambda status: sum(r.status == status for r in reqs)
    overdue = sum(r.status == RequestStatus.ISSUED and r.end_date < today for r in reqs)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pending review", count(RequestStatus.PENDING))
    c2.metric("Reserved", count(RequestStatus.RESERVED))
    c3.metric("On loan", count(RequestStatus.ISSUED))
    c4.metric("Overdue", overdue)

    st.markdown("#### Where to go")
    pages = PAGES[user.role]
    for col, (name, what) in zip(st.columns(len(pages)), pages):
        with col.container(border=True):
            st.markdown(f"**{name}**")
            st.caption(what)

    with st.expander("How a request moves through the system"):
        st.code(LIFECYCLE, language=None)
