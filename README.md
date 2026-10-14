# Library Management System: IIIT Hackathon

A Streamlit + SQLite prototype of a university library lending lifecycle:
**request → review → confirmed reservation → loan → return**, with copy-level availability that never double-books a physical copy.

> Status: the interface contract and the task split are done; implementation is in progress. Person 1 completes this README (see [docs/team/1.md](docs/team/1.md)).

## Setup (everyone, once)
Run every command **from the project root** (the folder containing `pyproject.toml`).
```bash
python -m venv .venv                 # optional but recommended
.venv\Scripts\activate               # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt      # = pip install -e ".[dev]"  (installs the lms package + pytest)
```
`pip install -e .` (editable install) is what makes `import lms` work from the app, the tests and the scripts. Skip it and you get `ModuleNotFoundError: No module named 'lms'`.

## Run
```bash
python -m streamlit run app/Home.py      # http://localhost:8501
python -m pytest                         # test suite
python -m lms.persistence.seed           # reset + reseed the demo DB (data/library.db)
```
Demo logins: `librarian / lib123`, and members `asha`, `ravi`, `meera`, `kiran` with password `pass123`.

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
├── docs/
│   ├── problem-statement.pdf
│   ├── BRD.md · PRD.md         # requirements                                   (P1)
│   ├── ASSUMPTIONS.md · PITCH.md                                                (P1, to write)
│   ├── ARCHITECTURE.md · TEST_EVIDENCE.md                                       (P7, to write)
│   └── team/1.md … 7.md        # per-person work split
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
[Problem statement](docs/problem-statement.pdf) · [BRD](docs/BRD.md) · [PRD](docs/PRD.md) · [Team tasks](docs/team/)
