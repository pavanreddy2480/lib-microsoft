"""Shared Streamlit helpers. CONTRACT FILE (owner: Person 1).

Every page starts with:
    from lms.ui.common import page_setup
    user = page_setup("Review Queue", Role.LIBRARIAN)   # or Role.MEMBER, or None = any logged-in user

and wraps every service call with run_action(...) so business errors are shown
clearly (st.error) instead of crashing.
"""
from __future__ import annotations

import secrets
from contextlib import closing
from datetime import date

import streamlit as st

from lms.domain import clock
from lms.domain.errors import BusinessRuleError
from lms.domain.models import Role, User


# Login survives a browser refresh: token -> user id, kept in server memory and
# echoed in the URL (?s=...). Demo-grade: anyone with the URL is logged in, and a
# server restart logs everyone out.
_SESSIONS: dict[str, int] = {}
_PARAM = "s"


def current_user() -> User | None:
    return st.session_state.get("user")


def remember_login(user: User) -> None:
    """Call right after a successful login."""
    token = secrets.token_urlsafe(16)
    _SESSIONS[token] = user.id
    st.session_state["user"] = user
    st.session_state["_token"] = token
    st.query_params[_PARAM] = token


def restore_login() -> None:
    """Re-attach the user after a refresh and keep the token in the URL across pages."""
    token = st.session_state.get("_token")
    if current_user() is not None and token:
        if st.query_params.get(_PARAM) != token:
            st.query_params[_PARAM] = token
        return
    token = st.query_params.get(_PARAM)
    user_id = _SESSIONS.get(token) if token else None
    if user_id is None:
        return
    from lms.persistence import db
    from lms.persistence import repository as repo
    with closing(db.get_conn()) as conn:
        user = repo.get_user(conn, user_id)
    if user is not None:
        st.session_state["user"] = user
        st.session_state["_token"] = token


def forget_login() -> None:
    _SESSIONS.pop(st.session_state.pop("_token", None), None)
    st.session_state.pop("user", None)
    st.query_params.pop(_PARAM, None)


def sidebar() -> None:
    """Logged-in user, business-date override (demo 'time travel'), logout."""
    user = current_user()
    with st.sidebar:
        st.markdown("### 📚 Library")
        if user:
            with st.container(border=True):
                role_colour = "blue" if user.role == Role.LIBRARIAN else "green"
                st.markdown(f"**{user.full_name}**  \n"
                            f"`{user.username}` :{role_colour}-badge[{user.role.value.title()}]")
                if st.button("Log out", width="stretch"):
                    forget_login()
                    st.rerun()
        new_today = st.date_input("Business date (today)", value=clock.business_today(),
                                  format="DD/MM/YYYY",
                                  help="Simulated 'today' used by every rule. Default 2026-08-01. "
                                       "Move it forward to issue or return books in the demo.")
        if new_today != clock.business_today():
            clock.set_business_today(new_today)
            st.rerun()


_CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
h1 {font-weight: 700;}
/* Neutral cards and metric tiles: no fixed colours, so they work in light and dark mode */
[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 10px;}
[data-testid="stMetric"] {
  border: 1px solid rgba(128, 128, 128, .25); border-radius: 10px; padding: 12px 16px;
}
[data-testid="stMetricValue"] {font-weight: 700;}
</style>
"""

# One colour per status, used everywhere a status is shown.
STATUS_COLOURS = {
    "PENDING": "orange", "RESERVED": "blue", "ISSUED": "violet",
    "RETURNED": "green", "REJECTED": "red", "CANCELLED": "gray", "OVERDUE": "red",
    "IN_SERVICE": "green", "DAMAGED": "red", "UNDER_REPAIR": "orange",
    "LOST": "red", "REFERENCE_ONLY": "gray", "RESTRICTED": "gray",
}


def status_badge(status) -> str:
    """Markdown badge for a RequestStatus / CopyStatus (or its string value)."""
    value = getattr(status, "value", status)
    return f":{STATUS_COLOURS.get(value, 'gray')}-badge[{value}]"


def apply_style() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_setup(title: str, role: Role | None = None) -> User:
    """Set title, draw sidebar, stop the page unless the right user is logged in."""
    st.set_page_config(page_title=f"LMS · {title}", page_icon="📚", layout="wide")
    apply_style()
    restore_login()
    sidebar()
    user = current_user()
    if user is None:
        st.warning("Please log in from the Home page first.")
        st.stop()
    if role is not None and user.role != role:
        st.error(f"This page is for {role.value.lower()}s only.")
        st.stop()
    st.title(title)
    st.caption(f"Signed in as **{user.full_name}** · {user.role.value.title()} · "
               f"business date {fmt_date(clock.business_today())}")
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
