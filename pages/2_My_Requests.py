"""My requests (MEMBER).  OWNER: Person 5 (see tasks/5.md).

TODO:
  user = page_setup("My Requests", Role.MEMBER)
  - repo.list_requests(conn, member_id=user.id) grouped: Active (PENDING/RESERVED/ISSUED) and History
  - columns: #id, Title, Copy, Start, Return by, Status, Decision note
  - "Cancel" button only for PENDING / RESERVED -> run_action(services.cancel_request, user, id)
  - REJECTED rows show the reason + hint "Create a new request to try again" (no edit button!)
  - expander "History" -> services.get_request_history(id)
  - ISSUED with end_date < business_today() -> show "OVERDUE" badge
"""
from lms.models import Role
from ui_common import page_setup

user = page_setup("My Requests", Role.MEMBER)
