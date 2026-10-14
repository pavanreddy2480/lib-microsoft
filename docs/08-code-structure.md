# 08 · Code Structure

> **Stage:** Design → Build · **Owner:** P1 (contract), everyone (follows it)
> **Prev:** [07 · Architecture](07-architecture.md) · **Next:** [09 · Development Plan](09-development-plan.md)

How the codebase is organised, where each kind of code goes, and the conventions that let 7 people work in parallel without stepping on each other.

---

## 1. Repository tree
```
lib-microsoft/
|-- pyproject.toml            package metadata, dependencies, pytest config (pythonpath=src)
|-- requirements.txt          "-e .[dev]"  -> installs lms (editable) + pytest
|-- .gitignore                caches, venv, data/*
|-- .gitattributes            LF line endings for every OS
|
|-- app/                      PRESENTATION (thin Streamlit scripts)
|   |-- Home.py               entry point: login + role-aware home ............ P1
|   `-- pages/                Streamlit auto-discovers these (number = menu order)
|       |-- 1_Catalog.py      member: availability + new request .............. P5
|       |-- 2_My_Requests.py  member: track / cancel / history ................ P5
|       |-- 3_Review_Queue.py librarian: approve / reject ..................... P6
|       |-- 4_Loans.py        librarian: issue / return ....................... P6
|       `-- 5_Inventory.py    librarian: copy status, demo reset .............. P6
|
|-- src/lms/                  CORE PACKAGE (import as `lms`)
|   |-- config.py             every path (DB, schema, data dir) ............... contract
|   |-- domain/               pure Python, no I/O
|   |   |-- models.py         enums, ALLOWED_TRANSITIONS, dataclasses ......... contract
|   |   |-- errors.py         BusinessRuleError + error codes ................. contract
|   |   |-- clock.py          business_today() ................................ contract
|   |   `-- security.py       hash_password() ................................. contract
|   |-- persistence/          SQLite only, no business rules
|   |   |-- schema.sql        tables, CHECKs, FKs, overlap triggers ........... contract
|   |   |-- db.py             get_conn, init_db, drop_all, transaction ........ P2
|   |   |-- repository.py     SQL <-> dataclasses ............................. P2
|   |   `-- seed.py           PDF data, reset_db, ensure_db ................... P3
|   |-- services/             ALL business rules live here
|   |   |-- auth.py           login, require_role ............................. P2
|   |   |-- availability.py   copy-level availability engine .................. P3
|   |   `-- lending.py        lifecycle state machine ......................... P4
|   `-- ui/
|       `-- common.py         page_setup, run_action, sidebar ................. contract
|
|-- tests/                    pytest; conftest.py gives a fresh seeded DB per test  P7
|-- docs/                     numbered stage docs 01-13, CONTEXT.md, team/1-7.md
`-- data/                     runtime SQLite DB (git-ignored, .gitkeep only)
```

## 2. Where does my code go?
| I need to… | Put it in | Not in |
|---|---|---|
| Add or change a status / transition | `domain/models.py` (contract: ask P1) | anywhere else |
| Add a new kind of refusal | `domain/errors.py` code + raise it in a **service** | the page |
| Write SQL | `persistence/repository.py` | services, pages |
| Decide whether something is **allowed** | `services/lending.py` or `services/availability.py` | pages, repository |
| Read data to **display** it | a page, via `repo.*` with `closing(db.get_conn())` | - |
| **Change** data | a page calls `lending.*` | a page calling `repo.update_*` directly |
| Show an error | `run_action(...)` from `lms.ui.common` | try/except in every page |
| Get "today" | `clock.business_today()` | `date.today()` |
| Build a file path | `lms.config` | `os.getcwd()`, relative strings |
| Add a test | `tests/test_<area>.py` | inside `src/` |

## 3. How one click travels through the code
Example: a librarian clicks **Approve** on request #7.
```
 app/pages/3_Review_Queue.py
   st.button("Approve", key="approve_7")
     -> run_action(lending.approve_request, user, 7, note)          lms/ui/common.py
          -> lending.approve_request(actor, 7, note)                lms/services/lending.py
               require_role(actor, LIBRARIAN)                       lms/services/auth.py
               with db.transaction() as conn:                       lms/persistence/db.py
                   req = repo.get_request(conn, 7)                  lms/persistence/repository.py
                   can_transition(PENDING, RESERVED)?               lms/domain/models.py
                   copy still IN_SERVICE? else find_free_copy(...)  lms/services/availability.py
                   repo.update_request_status(conn, 7, RESERVED)    -> SQLite (trigger checks IR1)
                   repo.insert_event(conn, 7, PENDING, RESERVED, ...)
               COMMIT
          <- Request(status=RESERVED)
     <- st.success(...)      or, on BusinessRuleError:  st.error(message)
   st.rerun()
```

## 4. Contract files (frozen)
```
 src/lms/config.py
 src/lms/domain/models.py   errors.py   clock.py   security.py
 src/lms/persistence/schema.sql
 src/lms/ui/common.py
 + the SIGNATURES (not bodies) of every stub function
```
Everyone codes against these at the same time. To change one:
1. Ask P1.
2. P1 announces the change to the whole team.
3. One person makes it, in a small commit of its own.

## 5. Conventions
**Imports:** use exactly these forms.
```python
from lms import config
from lms.domain import clock
from lms.domain.errors import BusinessRuleError, NO_COPY_AVAILABLE
from lms.domain.models import Role, RequestStatus, CopyStatus
from lms.persistence import db, seed
from lms.persistence import repository as repo
from lms.services import auth, availability, lending
from lms.ui.common import page_setup, run_action, fmt_date      # app/ only
```
**Naming**
- Modules and functions are `snake_case`. Classes and enums are `PascalCase`. Constants are `UPPER_CASE`.
- Service functions are verbs: `submit_request`, `approve_request`, `issue_loan`.
- Repository functions are data verbs: `get_*`, `list_*`, `insert_*`, `update_*`.
- Pages are named `N_Title.py` (N = menu order).

**Rules of thumb**
- Services take the acting `User` first (`actor`) and raise `BusinessRuleError` on any refusal.
- Repository functions take `conn` first and **never** raise business errors.
- Store dates as ISO text (`YYYY-MM-DD`) and handle them as `datetime.date` in Python.
- Use SQL `?` placeholders only.
- Every Streamlit button needs a unique `key=`, and `st.rerun()` follows a successful action.
- Keep functions short enough to explain out loud.

## 6. Ownership map
```
            P1         P2            P3              P4          P5          P6           P7
         +-------+ +----------+ +--------------+ +---------+ +---------+ +----------+ +---------+
 app/    |Home.py| |          | |              | |         | |pages 1-2| |pages 3-5 | |         |
 lms/    |       | |db.py     | |availability  | |lending  | |         | |          | |         |
         |       | |repository| |seed.py       | |         | |         | |          | |         |
         |       | |auth.py   | |              | |         | |         | |          | |         |
 tests/  |       | |          | |              | |         | |         | |          | |tests/*  |
 docs/   |01-06, | |          | |              | |         | |         | |          | |07,10,11 |
         |13,    | |          | |              | |         | |         | |          | |         |
         |README | |          | |              | |         | |         | |          | |         |
         +-------+ +----------+ +--------------+ +---------+ +---------+ +----------+ +---------+
 Contract files: P1 approves changes. Details: docs/team/N.md
```

## 7. Setup and commands (from the project root)
```bash
pip install -r requirements.txt          # once; makes `import lms` work everywhere
python -m streamlit run app/Home.py      # run the app
python -m pytest                         # run the tests
python -m lms.persistence.seed           # reset the demo DB
```
