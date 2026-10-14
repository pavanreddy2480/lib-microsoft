"""Shared Streamlit helpers. CONTRACT FILE (owner: Person 1).

Every page starts with:
    from ui_common import page_setup
    user = page_setup("Review Queue", Role.LIBRARIAN)   # or Role.MEMBER, or None = any logged-in user

and wraps every service call with run_action(...) so business errors are shown
clearly (st.error) instead of crashing.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from lms import clock
from lms.errors import BusinessRuleError
from lms.models import Role, User


def current_user() -> User | None:
    return st.session_state.get("user")


def sidebar() -> None:
    """Logged-in user, business-date override (demo 'time travel'), logout."""
    user = current_user()
    with st.sidebar:
        if user:
            st.markdown(f"**{user.full_name}**  \n`{user.username}` · {user.role.value}")
            if st.button("Log out"):
                st.session_state.pop("user", None)
                st.rerun()
        st.divider()
        new_today = st.date_input("Business date (today)", value=clock.business_today(),
                                  help="Simulated 'today' used by every rule. Default 2026-08-01.")
        if new_today != clock.business_today():
            clock.set_business_today(new_today)
            st.rerun()


def page_setup(title: str, role: Role | None = None) -> User:
    """Set title, draw sidebar, stop the page unless the right user is logged in."""
    st.set_page_config(page_title=f"LMS · {title}", layout="wide")
    sidebar()
    user = current_user()
    if user is None:
        st.warning("Please log in from the Home page first.")
        st.stop()
    if role is not None and user.role != role:
        st.error(f"This page is for {role.value.lower()}s only.")
        st.stop()
    st.title(title)
    return user


def run_action(fn, *args, success: str | None = None, **kwargs):
    """Call a service; on BusinessRuleError show st.error and return None."""
    try:
        result = fn(*args, **kwargs)
    except BusinessRuleError as err:
        st.error(err.message)
        return None
    if success:
        st.success(success)
    return result


def fmt_date(d: date | None) -> str:
    return d.strftime("%d %b %Y") if d else "-"
