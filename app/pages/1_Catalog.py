"""Catalog + new borrowing request (MEMBER).  OWNER: Person 5 (see docs/team/5.md).

Left: copy-level availability of every title for the chosen period (BR2).
Right: request panel - availability check with the reason (BR10), then submit.
The service makes every decision; the page only shows the result (BR4).
"""
import html
from contextlib import closing
from datetime import timedelta

import streamlit as st

from lms.domain import clock
from lms.domain.errors import BusinessRuleError
from lms.domain.models import Role
from lms.persistence import db
from lms.persistence import repository as repo
from lms.services import availability, lending
from lms.ui.common import bar, fmt_date, html_table, page_setup, pill, run_action, status_badge

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
        rows = []
        for item in catalog:
            res = item.result
            out = res.total_copies - res.total_in_service
            name = f"<b>{html.escape(item.title.title)}</b>"
            name += f'<span class="sub">{html.escape(item.title.category)}'
            name += f" · {out} out of service</span>" if out else "</span>"
            free = bar(res.free_count / res.total_copies if res.total_copies else 0)
            free += f"{res.free_count} of {res.total_copies}"
            state = pill("Available", "green") if res.available else pill("Unavailable", "red")
            rows.append([name, free, state])
        html_table(["Title", "Free for period", "Status"], rows)
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
