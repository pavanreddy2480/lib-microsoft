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
/* Clean tables (html_table): row dividers only, muted header, status pills */
.lms-table {width: 100%; border-collapse: collapse; font-size: .95rem; margin: .25rem 0 1rem 0;}
.lms-table th {text-align: left; font-weight: 600; font-size: .78rem; letter-spacing: .04em;
  text-transform: uppercase; opacity: .6; padding: 8px 10px;
  border-bottom: 1px solid rgba(128, 128, 128, .35);}
.lms-table td {padding: 10px; border-bottom: 1px solid rgba(128, 128, 128, .15); vertical-align: middle;}
.lms-table tr:hover td {background: rgba(128, 128, 128, .06);}
.lms-table .sub {display: block; font-size: .8rem; opacity: .6;}
.lms-table code {font-size: .85rem;}
.lms-pill {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .78rem;
  font-weight: 600; white-space: nowrap;}
.lms-bar {height: 6px; border-radius: 3px; background: rgba(128, 128, 128, .2); width: 110px;
  display: inline-block; vertical-align: middle; margin-right: 8px; overflow: hidden;}
.lms-bar > span {display: block; height: 100%; background: #3b82f6;}
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


_PILL_RGB = {"green": "34,160,90", "red": "220,53,69", "orange": "217,119,6",
             "blue": "59,130,246", "violet": "139,92,246", "gray": "120,120,120"}


def pill(text: str, colour: str = "gray") -> str:
    """Small rounded status label (HTML) for html_table cells."""
    import html
    rgb = _PILL_RGB.get(colour, _PILL_RGB["gray"])
    return (f'<span class="lms-pill" style="background: rgba({rgb}, .15); '
            f'color: rgb({rgb});">{html.escape(text)}</span>')


def status_pill(status) -> str:
    value = getattr(status, "value", status)
    return pill(value.replace("_", " ").title(), STATUS_COLOURS.get(value, "gray"))


def bar(fraction: float) -> str:
    pct = max(0, min(100, round(fraction * 100)))
    return f'<span class="lms-bar"><span style="width: {pct}%"></span></span>'


def html_table(columns: list[str], rows: list[list[str]]) -> None:
    """Render a clean table. Cells are HTML: escape plain text with html.escape first."""
    head = "".join(f"<th>{c}</th>" for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    st.markdown(f'<table class="lms-table"><thead><tr>{head}</tr></thead>'
                f"<tbody>{body}</tbody></table>", unsafe_allow_html=True)


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
