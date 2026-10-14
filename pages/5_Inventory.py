"""Inventory / copy status (LIBRARIAN).  OWNER: Person 6 (see tasks/6.md).

TODO:
  user = page_setup("Inventory", Role.LIBRARIAN)
  - table of all copies: Title, Copy code, Status, Note, current/next active commitment
  - change status form: copy -> new CopyStatus + note
      -> affected = run_action(services.set_copy_status, user, copy_id, status, note)
      -> show every AffectedRequest (MOVED -> st.info, CLOSED -> st.warning)
  - "Reset demo data" button (two-step confirm with a checkbox, no confirm() dialogs)
      -> seed.reset_db(); clock.reset_business_today(); st.rerun()
"""
from lms.models import Role
from ui_common import page_setup

user = page_setup("Inventory", Role.LIBRARIAN)
