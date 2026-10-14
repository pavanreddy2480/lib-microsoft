"""Catalog + new borrowing request (MEMBER).  OWNER: Person 5 (see docs/team/5.md).

TODO:
  user = page_setup("Catalog", Role.MEMBER)
  - date inputs: start (default business_today()), end (default start + 13 days)
  - table from availability.catalog_availability(conn, start, end):
      Title | Category | Total copies | In service | Free for period | Status/reason
  - expander per title: copies list (copy_code, status) from repo.list_copies
  - request form: select title -> "Check availability" shows check_availability(...).reason
    -> "Submit request" calls run_action(lending.submit_request, user, title_id, start, end,
       success="Request #<id> submitted - awaiting librarian review (PENDING).")
  - NEVER let an unavailable request through: the service rejects it, UI just shows the reason.
"""
from contextlib import closing
from datetime import timedelta

import streamlit as st

from lms.domain import clock
from lms.domain.models import Role
from lms.persistence import db
from lms.persistence import repository as repo
from lms.services import availability, lending
from lms.ui.common import fmt_date, page_setup, run_action

user = page_setup("Catalog", Role.MEMBER)
today = clock.business_today()
start = st.date_input("Start date", value=today)
end = st.date_input("Return date", value=start + timedelta(days=13))

with closing(db.get_conn()) as conn:
  titles = {title.id: title for title in repo.list_titles(conn)}
  copies = {copy.id: copy for copy in repo.list_copies(conn)}

  st.subheader("Catalog availability")
  catalog = run_action(availability.catalog_availability, conn, start, end)
  if catalog is not None:
    rows = []
    for item in catalog:
      result = item.result
      rows.append(
        {
          "Title": item.title.title,
          "Category": item.title.category,
          "Total": result.total_copies,
          "In service": result.total_in_service,
          "Free for period": result.free_count,
          "Availability": ("✅ Available" if result.available else "❌ Not available"),
          "Note": result.reason,
        }
      )
    st.dataframe(rows, width="stretch", hide_index=True)

  with st.expander("Copies by title"):
    for title in titles.values():
      st.markdown(f"**{title.title}**")
      title_copies = [copy for copy in copies.values() if copy.title_id == title.id]
      st.write(
        [
          {"Copy": copy.copy_code, "Status": copy.status.value}
          for copy in title_copies
        ]
      )

  st.subheader("Request a book")
  if not titles:
    st.info("No titles are currently available in the catalog.")
  else:
    selected_title = st.selectbox(
      "Title", list(titles.values()), format_func=lambda title: title.title
    )
    result = run_action(
      availability.check_availability,
      conn,
      selected_title.id,
      start,
      end,
    )
    if result is not None:
      if result.available:
        st.success(
          f"Available: {result.free_count} copy/copies free from "
          f"{fmt_date(start)} to {fmt_date(end)}."
        )
      else:
        st.error(result.reason)

      if st.button("Submit request", disabled=not result.available):
        request = run_action(
          lending.submit_request,
          user,
          selected_title.id,
          start,
          end,
        )
        if request is not None:
          st.success(
            f"Request #{request.id} submitted - awaiting librarian review (PENDING)."
          )
