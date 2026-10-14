"""Home / login page.  OWNER: Person 1 (see docs/team/1.md).

Run from the project root:  python -m streamlit run app/Home.py

TODO (Person 1):
  - st.set_page_config + seed.ensure_db() on start
    (imports: from lms.persistence import seed; from lms.services import auth;
              from lms.ui.common import sidebar, current_user)
  - if not logged in: login form (username, password) -> auth.login -> st.session_state["user"]
    show demo credentials hint (librarian/lib123, asha/pass123)
  - if logged in: sidebar() from lms.ui.common + a short role-specific welcome:
      MEMBER    -> "Go to Catalog to request a book, My Requests to track/cancel"
      LIBRARIAN -> "Review Queue, Loans, Inventory"
  - show the lifecycle diagram (PENDING -> RESERVED -> ISSUED -> RETURNED, REJECTED, CANCELLED)
"""
import streamlit as st

st.set_page_config(page_title="Library Management System", layout="wide")
st.title("Library Management System")
st.info("Login page not implemented yet - see docs/team/1.md")
