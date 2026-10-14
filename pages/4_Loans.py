"""Reservations -> issue, loans -> return (LIBRARIAN).  OWNER: Person 6 (see tasks/6.md).

TODO:
  user = page_setup("Loans", Role.LIBRARIAN)
  Tab "Confirmed reservations" (RESERVED):
    - Issue -> run_action(services.issue_loan, user, id)
    - Cancel -> run_action(services.cancel_request, user, id, note)
  Tab "Active loans" (ISSUED): OVERDUE badge if end_date < business_today()
    - Return: select condition (CopyStatus, default IN_SERVICE) + note
      -> res = run_action(services.return_loan, user, id, condition, note)
      -> if res: request, affected = res; show each AffectedRequest (MOVED / CLOSED) with st.warning
  Tab "All requests": filterable table of every request + history expander
"""
from lms.models import Role
from ui_common import page_setup

user = page_setup("Loans", Role.LIBRARIAN)
