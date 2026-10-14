"""Shared Streamlit helpers. CONTRACT FILE (owner: Person 1).

Every page starts with:
    from lms.ui.common import page_setup
    user = page_setup("Review Queue", Role.LIBRARIAN)   # or Role.MEMBER, or None = any logged-in user

and wraps every service call with run_action(...) so business errors are shown
clearly (st.error) instead of crashing.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from lms.domain import clock
from lms.domain.errors import BusinessRuleError
from lms.domain.models import Role, User


def current_user() -> User | None:
    return st.session_state.get("user")


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
                    st.session_state.pop("user", None)
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

/* Titles: indigo -> violet -> pink gradient text */
h1 {
  font-weight: 800 !important;
  background: linear-gradient(90deg, #4f46e5, #7c3aed 55%, #db2777);
  -webkit-background-clip: text; background-clip: text; color: transparent !important;
}
h3, h4 {color: #3730a3;}

/* Sidebar: soft indigo gradient */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #eef2ff 0%, #f5f3ff 55%, #fdf2f8 100%);
}

/* Bordered containers become lifted cards */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 14px; background: #ffffff;
  box-shadow: 0 1px 3px rgba(30, 27, 75, .06), 0 6px 18px rgba(79, 70, 229, .06);
  transition: box-shadow .15s ease, transform .15s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 0 2px 6px rgba(30, 27, 75, .08), 0 10px 26px rgba(79, 70, 229, .12);
}

/* Metric tiles: one colour each (pending, reserved, on loan, overdue) */
[data-testid="stMetric"] {
  background: #ffffff; border-radius: 14px; padding: 14px 18px;
  border-left: 6px solid #6366f1; box-shadow: 0 4px 14px rgba(79, 70, 229, .08);
}
[data-testid="stColumn"]:nth-of-type(1) [data-testid="stMetric"] {border-left-color: #f59e0b;}
[data-testid="stColumn"]:nth-of-type(2) [data-testid="stMetric"] {border-left-color: #3b82f6;}
[data-testid="stColumn"]:nth-of-type(3) [data-testid="stMetric"] {border-left-color: #8b5cf6;}
[data-testid="stColumn"]:nth-of-type(4) [data-testid="stMetric"] {border-left-color: #ef4444;}
[data-testid="stMetricValue"] {font-weight: 800; color: #1e1b4b;}

/* Primary buttons: gradient */
button[kind="primary"], button[kind="primaryFormSubmit"] {
  background: linear-gradient(90deg, #4f46e5, #7c3aed) !important;
  border: none !important; color: #fff !important;
}
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {filter: brightness(1.08);}

/* Tables and expanders: rounded */
[data-testid="stDataFrame"], [data-testid="stExpander"] {border-radius: 12px; overflow: hidden;}

/* Coloured banner used on Home */
.lms-banner {
  padding: 22px 26px; border-radius: 16px; color: #fff; margin-bottom: 1rem;
  background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
  box-shadow: 0 10px 30px rgba(124, 58, 237, .25);
}
.lms-banner h2 {color: #fff; margin: 0 0 4px 0; font-weight: 800;}
.lms-banner p {margin: 0; opacity: .92;}
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


def banner(title: str, subtitle: str = "") -> None:
    """Coloured gradient banner (plain text only: escaped)."""
    import html
    st.markdown(f'<div class="lms-banner"><h2>{html.escape(title)}</h2>'
                f'<p>{html.escape(subtitle)}</p></div>', unsafe_allow_html=True)


def page_setup(title: str, role: Role | None = None) -> User:
    """Set title, draw sidebar, stop the page unless the right user is logged in."""
    st.set_page_config(page_title=f"LMS · {title}", page_icon="📚", layout="wide")
    apply_style()
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
