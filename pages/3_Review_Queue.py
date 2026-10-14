"""Review queue (LIBRARIAN).  OWNER: Person 6 (see tasks/6.md).

TODO:
  user = page_setup("Review Queue", Role.LIBRARIAN)
  - repo.list_requests(conn, statuses=[PENDING]) oldest first
  - per row: member name, title, allocated copy code, period, created_at
  - Approve (optional note) -> run_action(services.approve_request, user, id, note)
  - Reject (reason text REQUIRED) -> run_action(services.reject_request, user, id, reason)
  - st.rerun() after a successful action
"""
from lms.models import Role
from ui_common import page_setup

user = page_setup("Review Queue", Role.LIBRARIAN)
