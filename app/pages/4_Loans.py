"""Reservations -> issue, loans -> return (LIBRARIAN).  OWNER: Person 6 (see docs/team/6.md).

TODO:
  user = page_setup("Loans", Role.LIBRARIAN)
  Tab "Confirmed reservations" (RESERVED):
    - Issue -> run_action(lending.issue_loan, user, id)
    - Cancel -> run_action(lending.cancel_request, user, id, note)
  Tab "Active loans" (ISSUED): OVERDUE badge if end_date < business_today()
    - Return: select condition (CopyStatus, default IN_SERVICE) + note
      -> res = run_action(lending.return_loan, user, id, condition, note)
      -> if res: request, affected = res; show each AffectedRequest (MOVED / CLOSED) with st.warning
  Tab "All requests": filterable table of every request + history expander
"""
from lms.domain.models import Role
from lms.ui.common import page_setup

user = page_setup("Loans", Role.LIBRARIAN)
