# Library Management System: IIIT Hackathon

A Streamlit + SQLite prototype of a university library lending lifecycle:
**request → review → confirmed reservation → loan → return**, with copy-level availability that never double-books a physical copy.

> **New to the project? Read [docs/CONTEXT.md](docs/CONTEXT.md) first.** · Pitch and demo script: [docs/13-pitch.md](docs/13-pitch.md)

## Quick start (about 2 minutes)
**Prerequisites:** Python **3.10+** and `pip`. Nothing else: SQLite ships with Python, and no internet is needed after the install.

Run every command **from the project root** (the folder containing `pyproject.toml`).
```bash
python -m venv .venv                 # optional but recommended
.venv\Scripts\activate               # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt      # = pip install -e ".[dev]"  (installs the lms package + pytest)
python -m streamlit run app/Home.py  # opens http://localhost:8501
```
The database (`data/library.db`) is created and seeded automatically on first start.

| Login | Password | Role |
|---|---|---|
| `librarian` | `lib123` | LIBRARIAN: Review Queue, Loans, Inventory |
| `asha`, `ravi`, `meera`, `kiran` | `pass123` | MEMBER: Catalog, My Requests |

"Today" is a **business date**, 01 Aug 2026 by default, so the seed data from the problem statement makes sense. Change it in the sidebar to "move time" in a demo.

## Other commands
```bash
python -m pytest                         # test suite (fresh seeded temp DB per test)
python -m lms.persistence.seed           # reset + reseed the demo DB (also: Inventory → Reset demo data)
```
`pip install -e .` (editable install) is what makes `import lms` work from the app, the tests and the scripts. Skip it and you get `ModuleNotFoundError: No module named 'lms'`.

## Scope
**In:** login with two roles; a catalog with copy-level availability for chosen dates; submitting a request with validation and an explained refusal; a review queue (approve, or reject with a reason); cancel or withdraw; issue and return with the copy's condition; inventory status changes that move or close affected bookings; an audit trail per request; seeded data from the problem statement plus a demo reset; automated tests.

**Excluded (on purpose):** fines, renewals, waitlists and holds queues, email or SMS notifications, alternative-book suggestions and partial fulfilment (excluded by the brief), multiple branches, barcodes or RFID, SSO, cloud deployment, and production-grade security. The reasons are in [docs/04-assumptions-and-scope.md](docs/04-assumptions-and-scope.md).

## Key trade-offs
| Choice | Benefit | Cost |
|---|---|---|
| A copy is committed at **submission** (PENDING holds a copy) | Rejection really "releases" a copy (BR7); no overbooking during review | Unreviewed requests can block others |
| Availability is **computed** from active requests, not stored | Cancel, reject and return free the copy automatically | A query instead of a flag (negligible at this scale) |
| App check **plus** a SQLite trigger against overlaps | A code bug still can't double-book a copy | The trigger doesn't know about overdue extensions |
| **First-fit** allocation (lowest copy code) | Deterministic and explainable | Can refuse a request that a reshuffle would fit |
| Streamlit + SQLite | Runs on a laptop with one install | Single-user-scale concurrency |

## Known limitations
- Login is **demo-grade**: sha256 with one static salt, no lockout, and the session lasts only while the browser tab is open.
- The business date is **global** to the running app: two browsers share one "today".
- Members are not notified when a booking is moved or closed. They see it in My Requests.
- An overdue loan blocks its copy only up to *today*, so a booking starting after today is still accepted.
- See [docs/05-critique-and-open-questions.md](docs/05-critique-and-open-questions.md) for the full self-critique.

## Project layout
```
lib-microsoft/
├── pyproject.toml              # package metadata, dependencies, pytest config
├── requirements.txt            # "-e .[dev]" (pyproject.toml is the single source of truth)
├── app/                        # PRESENTATION: thin Streamlit scripts, no business rules
│   ├── Home.py                 #   entry point: login + role-aware home        (P1)
│   └── pages/
│       ├── 1_Catalog.py        #   member: availability + new request          (P5)
│       ├── 2_My_Requests.py    #   member: track / cancel                      (P5)
│       ├── 3_Review_Queue.py   #   librarian: approve / reject                 (P6)
│       ├── 4_Loans.py          #   librarian: issue / return                   (P6)
│       └── 5_Inventory.py      #   librarian: copy status, demo reset          (P6)
├── src/lms/                    # CORE PACKAGE (installed with pip install -e .)
│   ├── config.py               #   all paths (DB, schema, data dir)            (contract)
│   ├── domain/                 #   pure: no I/O
│   │   ├── models.py           #     state model, enums, transitions, dataclasses (contract)
│   │   ├── errors.py           #     BusinessRuleError + codes                 (contract)
│   │   ├── clock.py            #     business date                             (contract)
│   │   └── security.py         #     hash_password                             (contract)
│   ├── persistence/            #   SQLite only, no business rules
│   │   ├── schema.sql          #     tables + no-overlap triggers              (contract)
│   │   ├── db.py               #     connection, transaction()                 (P2)
│   │   ├── repository.py       #     SQL → dataclasses                         (P2)
│   │   └── seed.py             #     PDF initial data, reset                   (P3)
│   ├── services/               #   business rules
│   │   ├── auth.py             #     login, role check                         (P2)
│   │   ├── availability.py     #     copy-level availability engine            (P3)
│   │   └── lending.py          #     lifecycle state machine                   (P4)
│   └── ui/
│       └── common.py           #   page_setup / run_action / sidebar           (contract)
├── tests/                      # pytest: fresh seeded DB per test              (P7)
├── docs/                       # numbered, one file per stage (index: docs/README.md)
│   ├── CONTEXT.md              #   start here
│   ├── 01-…05-*.md             #   problem, stakeholders, rules, assumptions, critique  (P1)
│   ├── 06-prd.md               #   product requirements                       (P1)
│   ├── 07-…10-*.md             #   architecture, code structure, plan, edge cases
│   ├── 11-test-evidence.md     #   real pytest output + manual checklist      (P7)
│   ├── 12-iteration-log.md
│   ├── 13-pitch.md             #   2 slides + demo script                     (P1)
│   ├── problem-statement.pdf
│   └── team/1.md … 7.md        #   per-person work split
└── data/                       # runtime SQLite DB (git-ignored)
```
**Dependency direction (one way only):** `app/ → lms.ui → lms.services → lms.persistence → lms.domain`. `domain` imports nothing from the project. Only `app/` and `lms.ui` import Streamlit. The UI never writes SQL; it calls `lending.*`.

## Import convention (use exactly these)
```python
from lms import config
from lms.domain import clock
from lms.domain.errors import BusinessRuleError            # + error codes
from lms.domain.models import Role, RequestStatus, CopyStatus, ...
from lms.persistence import db, seed
from lms.persistence import repository as repo
from lms.services import auth, availability, lending
from lms.ui.common import page_setup, run_action           # app/ pages only
```

## Git workflow
- One branch per person: `p1-docs-shell`, `p2-persistence`, `p3-availability`, `p4-services`, `p5-member-ui`, `p6-librarian-ui`, `p7-tests`.
- Edit only the files you own (see `docs/team/N.md`). Changing a **contract** file needs P1's approval and an announcement to the team.
- Small commits. P1 merges in the order P2 → P3 → P4 → P5/P6 → P7.
- `.gitattributes` normalises line endings to LF, so Windows editors don't create whole-file diffs.

## Docs
**[Start here: CONTEXT](docs/CONTEXT.md)** · [Docs index](docs/README.md) · [Problem statement](docs/problem-statement.pdf) · [Rules](docs/03-business-rules.md) · [Assumptions & scope](docs/04-assumptions-and-scope.md) · [PRD](docs/06-prd.md) · [Architecture](docs/07-architecture.md) · [Test evidence](docs/11-test-evidence.md) · [Pitch](docs/13-pitch.md) · [Team tasks](docs/team/)
