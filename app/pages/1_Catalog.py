"""Catalog + new borrowing request (MEMBER).  OWNER: Person 5 (see docs/team/5.md).

Left: copy-level availability of every title for the chosen period (BR2).
Right: request panel - availability check with the reason (BR10), then submit.
The service makes every decision; the page only shows the result (BR4).
"""
from contextlib import closing
from datetime import timedelta

import streamlit as st

from lms.domain import clock
from lms.domain.errors import BusinessRuleError
from lms.domain.models import Role
from lms.persistence import db
from lms.persistence import repository as repo
from lms.services import availability, lending
from lms.ui.common import fmt_date, page_setup, run_action, status_badge

user = page_setup("Catalog", Role.MEMBER)
today = clock.business_today()

d1, d2, _ = st.columns([1, 1, 2])
start = d1.date_input("Start date", value=today, format="DD/MM/YYYY")
end = d2.date_input("Return by", value=start + timedelta(days=13), format="DD/MM/YYYY")

try:
    availability.validate_period(start, end, today)
except BusinessRuleError as err:
    st.error(err.message)
    st.caption("Adjust the dates above to see availability.")
    st.stop()

period = f"{fmt_date(start)} → {fmt_date(end)}"

with closing(db.get_conn()) as conn:
    titles = {t.id: t for t in repo.list_titles(conn)}
    copies = repo.list_copies(conn)
    catalog = availability.catalog_availability(conn, start, end)

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("Availability")
        st.caption(f"Free copies for the whole period {period}")
        st.dataframe(
            [
                {
                    "Title": item.title.title,
                    "Category": item.title.category,
                    "Free": item.result.free_count,
                    "In service": item.result.total_in_service,
                    "Total": item.result.total_copies,
                    "Status": "✅ Available" if item.result.available else "❌ Unavailable",
                }
                for item in catalog
            ],
            hide_index=True,
            width="stretch",
            column_config={
                "Title": st.column_config.TextColumn(width="large"),
                "Free": st.column_config.NumberColumn(help="Copies free for the whole period"),
                "In service": st.column_config.NumberColumn(help="Copies that can be lent at all"),
            },
        )
        with st.expander("Copies by title"):
            for title in titles.values():
                badges = " ".join(
                    f"`{c.copy_code}` {status_badge(c.status)}"
                    for c in copies if c.title_id == title.id
                )
                st.markdown(f"**{title.title}**  \n{badges}")

    with right, st.container(border=True):
        st.subheader("Request a book")
        if not titles:
            st.info("No titles in the catalog yet.")
            st.stop()
        selected = st.selectbox("Title", list(titles.values()),
                                format_func=lambda t: t.title)
        result = availability.check_availability(conn, selected.id, start, end)
        if result.available:
            st.success(f"**{result.free_count}** of {result.total_in_service} copies free "
                       f"for {period}.")
        else:
            st.error(result.reason)

        if st.button("Submit request", type="primary", width="stretch",
                     disabled=not result.available):
            request = run_action(lending.submit_request, user, selected.id, start, end)
            if request is not None:
                st.success(f"Request #{request.id} submitted - awaiting librarian review "
                           "(PENDING).")
                st.caption("Track it on the **My Requests** page.")
        st.caption("A specific copy is held for you as soon as you submit. "
                   "A librarian then approves or rejects it.")
