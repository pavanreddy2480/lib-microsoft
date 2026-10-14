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
from lms.domain.models import Role
from lms.ui.common import page_setup

user = page_setup("Catalog", Role.MEMBER)
