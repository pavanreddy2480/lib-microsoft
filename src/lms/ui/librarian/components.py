"""Streamlit building blocks shared by the three librarian pages.

Thin rendering only. Decisions come from `presenters`; calls go through the port.
"""
from __future__ import annotations

from typing import Callable, Iterable

import streamlit as st

from lms.ui.common import run_action
from lms.ui.librarian import presenters
from lms.ui.librarian.views import AffectedRow

_FLASH_KEY = "librarian_flash"


def flash(level: str, message: str) -> None:
    """Queue a message that survives the st.rerun() following a successful action."""
    st.session_state.setdefault(_FLASH_KEY, []).append((level, message))


def show_flash() -> None:
    """Render and clear queued messages. Call once near the top of every page."""
    for level, message in st.session_state.pop(_FLASH_KEY, []):
        getattr(st, level, st.info)(message)


def flash_affected(rows: Iterable[AffectedRow]) -> None:
    for row in rows:
        flash(presenters.outcome_severity(row), presenters.affected_text(row))


def act(fn: Callable, *args, success: str | Callable | None = None, **kwargs) -> bool:
    """Run a port command through `run_action`; on success flash + rerun.

    `success` may be a message or a callable(result) -> None for custom flashing.
    Returns False when the business rule refused (the error is already on screen).
    """
    result = run_action(fn, *args, **kwargs)
    if result is None:
        return False
    if callable(success):
        success(result)
    elif success:
        flash("success", success)
    st.rerun()
    return True  # pragma: no cover  (st.rerun raises)
