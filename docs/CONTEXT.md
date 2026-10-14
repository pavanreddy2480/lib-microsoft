# Project Context: read this first

This is the one-page briefing for every team member, and for any AI assistant (Copilot, Claude, GPT) you use while coding. It explains **what** we are building, **why** it is shaped this way, the **decisions already made**, and **how to work** without breaking each other's code.

> **Using an AI assistant?** Paste this file plus your own `docs/team/N.md` into the chat before asking for code. Tell it: *"Follow CONTEXT.md. Only edit the files I own. Do not change contract files."*

---

## 1. The situation
- **Event:** an IIIT hackathon. **90 minutes, a team of 7.** Python + Streamlit, run locally. No cloud, no paid services, no external APIs.
- **Problem:** a university library manages book requests, reservations, loans and returns on registers and spreadsheets. As a result, copies get double-promised, students request books without checking availability, nobody can see request status, cancelled or returned copies stay "unavailable", and damaged copies aren't tracked.
- **Goal:** a working prototype covering the lending lifecycle **request → review → confirmed reservation → loan → return**, with correct copy-level availability and clear validation errors.
- **Source of truth for requirements:** [problem-statement.pdf](problem-statement.pdf).

### How we are scored (from the PDF)
| Criterion | Weight | What it means for us |
|---|---|---|
| Problem understanding | 20% | Stakeholders, workflows, rules and scope: see [docs 01-05](README.md) |
| Implementation & completeness | 20% | Working flows, clean structure, code we can explain |
| AI usage | 20% | We direct, question and validate the AI. We don't blindly paste. |
| Collaboration & communication | 20% | Visible git history per person, plus the 2-slide pitch |
| Quiz | 20% | Already done |

**Every member may be asked to explain** their contribution, one business rule, one part of the solution, one assumption or trade-off, and how they validated their work. Your `docs/team/N.md` ends with "Be ready to explain". Prepare that.

> "A smaller, reliable and well-explained solution may score higher than a larger application containing generated code that the team cannot validate or explain." (PDF)

---

## 2. Business rules (from the PDF; never violate these)
| ID | Rule |
|---|---|
| BR1 | A request = one member + one book title + start date + expected return date. |
| BR2 | Availability is computed from **individual physical copies**, not a title-level count. |
| BR3 | A copy must **never** have overlapping active commitments (pending request, reservation or loan). |
| BR4 | A request is **refused before submission** if no copy is free for the **whole** period. |
| BR5 | Damaged, under-repair, lost, reference-only and restricted copies are **never** allocated. |
| BR6 | Every submitted request is **reviewed** by a librarian before it becomes a reservation or loan. |
| BR7 | Rejection **closes** the request and releases the copy. A rejected request is never edited or resubmitted; the member creates a new one. |
| BR8 | A confirmed reservation can be **cancelled before issue**, releasing the copy. |
| BR9 | A **return** releases the copy, unless the copy is marked unavailable during the return. |
| BR10 | Every refusal **tells the user why**. No partial fulfilment and no alternative-book suggestions. |

---

## 3. Decisions already made (do not reopen them during the build)
| Topic | Decision | Why |
|---|---|---|
| Stack | Python 3.10+, Streamlit, SQLite (stdlib `sqlite3`) | The workload is mostly reads, there are no concurrent writers at this scale, and it needs no setup. Postgres wasn't installed. |
| Copy commitment | A **specific copy is allocated at submission**. A PENDING request already holds it. | BR3 lists "active borrowing requests" as commitments, and BR7 says rejection "releases" the copy. |
| "Today" | A **business date**, default **2026-08-01**, changeable in the sidebar | The PDF data is dated Aug 2026. This keeps it meaningful and lets the demo "move time" to issue or return. |
| Dates | **Inclusive**. A copy due 4 Aug can be lent from 5 Aug. | Simple and safe |
| Max period | **30 days** inclusive. The start can't be in the past. | Team decision |
| Duplicates | A member can't hold overlapping active requests for the same title | Stops hoarding |
| Approval | Approve → **RESERVED**. Issue is a separate step, only when start ≤ today ≤ end. | Matches the PDF wording "confirmed reservation or loan" |
| Overdue | An ISSUED loan blocks its copy until it is actually returned, even past its end date | The book physically isn't on the shelf |
| Copy goes out of service with future bookings | **Auto-move** each booking to another free copy. If none is free, **close** it (PENDING→REJECTED, RESERVED→CANCELLED) with a reason. Always shown to the librarian. | "Existing commitments must not be silently overwritten" |
| Member withdraw | A member may cancel their own PENDING request too | Same code path as cancel |
| Auth | **Simple login**: username + password, roles MEMBER and LIBRARIAN, sha256 hash | Makes identity and librarian-only actions real. Demo-grade, documented as a limitation. |
| Seed data gaps | Issue start dates aren't in the PDF, so they are set to due date − 14 days. "1 issued + 1 reserved" means **two different copies**. | Documented assumption |

Out of scope: fines, renewals, waitlists, notifications, alternative suggestions, multiple branches, barcodes, SSO, production security. A bonus feature comes only after the core demo works, and only with team agreement.

---

## 4. The state model (one model everywhere: UI, code, DB, tests)
**Request status:** one request row covers the whole lifecycle.
```
PENDING ──approve──▶ RESERVED ──issue──▶ ISSUED ──return──▶ RETURNED
   │                    │
   ├──reject──▶ REJECTED └──cancel──▶ CANCELLED
   └──cancel (member withdraw)──▶ CANCELLED
```
- **Active (holds the copy):** `PENDING`, `RESERVED`, `ISSUED`
- **Terminal (copy released):** `REJECTED`, `CANCELLED`, `RETURNED`. Nothing leaves a terminal state.
- "Releasing a copy" is **not** a separate step. It happens automatically when the request leaves an active status.
- Legal moves live **only** in `ALLOWED_TRANSITIONS` in `src/lms/domain/models.py`.

**Copy status:** the physical condition, stored on the copy.
`IN_SERVICE` (the only allocatable one) · `DAMAGED` · `UNDER_REPAIR` · `LOST` · `REFERENCE_ONLY` · `RESTRICTED`

**When a copy is free for [start, end]:** it is `IN_SERVICE` **and** no active request on it overlaps. The overlap test is `a.start <= b.end and b.start <= a.end`. For an ISSUED request, its end is `max(end_date, today)`.

**Two safety layers for BR3:**
1. `availability.find_free_copy()` checks before allocating, inside a `BEGIN IMMEDIATE` transaction.
2. A **SQLite trigger** (`schema.sql`) refuses any overlapping active row even if the code has a bug. This is tested and works.

---

## 5. Architecture
```
app/Home.py, app/pages/*        Streamlit pages: display + call services, no rules
        │
lms.ui.common                   page_setup (login/role guard), run_action (shows errors), sidebar
        │
lms.services                    auth · availability (copy engine) · lending (state machine)
        │
lms.persistence                 db (connection, transaction) · repository (SQL only) · seed · schema.sql
        │
lms.domain                      models (state model) · errors · clock · security   (pure, no I/O)
```
- **Dependencies point downward only.** `domain` imports nothing from the project. Only `app/` and `lms.ui` import Streamlit.
- **Business rules live only in `services/`.** Pages never decide whether something is allowed; they call `lending.*` and show the result.
- **All paths come from `lms/config.py`:** DB at `<root>/data/library.db`, schema at `src/lms/persistence/schema.sql`. Override with `LMS_DB_PATH` or `LMS_DATA_DIR`. Never build paths from the current folder.
- **Errors:** every rule violation raises `BusinessRuleError(code, message)`. The UI wraps calls in `run_action(...)`, which shows `st.error(message)` and never a stack trace.

### The tables
`users` · `titles` · `copies` (status) · `requests` (member, title, copy, start, end, status, decision_note, timestamps) · `request_events` (an audit trail: every status change records who, when, from, to and a note).

### Error codes (`lms/domain/errors.py`)
`INVALID_DATES` · `START_IN_PAST` · `PERIOD_TOO_LONG` · `NO_COPY_AVAILABLE` · `DUPLICATE_REQUEST` · `INVALID_TRANSITION` · `NOT_AUTHORIZED` · `NOT_FOUND` · `ISSUE_NOT_ALLOWED` · `REASON_REQUIRED` · `LOGIN_FAILED`

### Main service API (`lms.services.lending`); `actor` is the logged-in `User`
| Function | Transition | Who |
|---|---|---|
| `submit_request(actor, title_id, start, end)` | → PENDING (allocates a copy) | Member |
| `approve_request(actor, request_id, note="")` | PENDING → RESERVED | Librarian |
| `reject_request(actor, request_id, reason)` | PENDING → REJECTED (reason required) | Librarian |
| `cancel_request(actor, request_id, note="")` | PENDING/RESERVED → CANCELLED | Owner or librarian |
| `issue_loan(actor, request_id)` | RESERVED → ISSUED | Librarian |
| `return_loan(actor, request_id, condition, note)` | ISSUED → RETURNED (+ copy condition) | Librarian |
| `set_copy_status(actor, copy_id, status, note)` | copy status change + reallocation | Librarian |
| `get_request_history(request_id)` | the audit trail | Anyone |

Availability helpers (`lms.services.availability`): `check_availability(conn, title_id, start, end)` returns the counts and the reason, and `catalog_availability(conn, start, end)` returns every title. Full signatures and docstrings are in the source files. **The docstrings are the spec.**

---

## 6. Repository layout and owners
```
app/Home.py                         P1   login + home
app/pages/1_Catalog.py, 2_My_Requests.py                 P5   member screens
app/pages/3_Review_Queue.py, 4_Loans.py, 5_Inventory.py  P6   librarian screens
src/lms/config.py                   contract (all paths)
src/lms/domain/*                    contract (models, errors, clock, security)
src/lms/persistence/schema.sql      contract
src/lms/persistence/db.py, repository.py    P2
src/lms/services/auth.py            P2
src/lms/services/availability.py, persistence/seed.py   P3
src/lms/services/lending.py         P4
src/lms/ui/common.py                contract (P1 approves changes)
tests/*                             P7
docs/01-06, 08, 09, 12, 13 (problem → PRD, plan, log, pitch)  P1
docs/07, 10, 11 (architecture, edge cases, test evidence)   P7
```
| # | Role | Your instructions |
|---|---|---|
| 1 | PM / BA + integration lead | [team/1.md](team/1.md) |
| 2 | Persistence | [team/2.md](team/2.md) |
| 3 | Availability engine + seed | [team/3.md](team/3.md) |
| 4 | Lifecycle services | [team/4.md](team/4.md) |
| 5 | Member UI | [team/5.md](team/5.md) |
| 6 | Librarian UI | [team/6.md](team/6.md) |
| 7 | QA / tests + bonus | [team/7.md](team/7.md) |

**Contract files** (`config.py`, `domain/*`, `schema.sql`, `ui/common.py`) are frozen. To change one, ask P1, who announces it to the whole team, because everyone codes against them.

---

## 7. Current status
- ✅ The interfaces are done: state model, schema with a tested overlap trigger, error codes, business date, paths, UI helpers, test fixtures, the numbered stage docs (01-12, see [README.md](README.md)), and the team task files.
- ✅ The app starts. Every page loads and shows the login guard.
- ⏳ **Everything else is a stub** (`raise NotImplementedError`). That is your work.
- ⏳ No tests exist yet (P7 writes them first, against the contract).

### Dependency order (who unblocks whom)
```
P2 persistence ─┐
                ├─▶ P4 services ─▶ P5 / P6 screens work end-to-end ─▶ P7 tests go green
P3 availability ┘
P1 docs + login shell and P7 test writing run in parallel from the start
```
If you are blocked, build against the documented signatures with fake data, then swap in the real calls after the merge.

### Timeline
| Time | Activity |
|---|---|
| T+0–15 | Interfaces (done) |
| T+15–35 | P2 and P3 build and **merge by T+35** |
| T+35–55 | P4 merges by T+50. P5 and P6 integrate by T+55. |
| T+55–70 | Integration and tests green |
| T+70–80 | Fixes, test evidence |
| T+80–90 | Pitch + demo rehearsal |

---

## 8. How to work
**Setup (once, from the project root):**
```bash
pip install -r requirements.txt          # installs the lms package (editable) + pytest
python -m streamlit run app/Home.py      # run the app → http://localhost:8501
python -m pytest                         # run tests
python -m lms.persistence.seed           # reset the demo database
```
If you see `ModuleNotFoundError: No module named 'lms'`, you skipped the install step.

**Imports (use exactly these):**
```python
from lms import config
from lms.domain import clock
from lms.domain.errors import BusinessRuleError
from lms.domain.models import Role, RequestStatus, CopyStatus
from lms.persistence import db, seed
from lms.persistence import repository as repo
from lms.services import auth, availability, lending
from lms.ui.common import page_setup, run_action          # pages only
```

**Coding rules:**
1. Use `clock.business_today()` for "today". Never use `date.today()`.
2. Every write goes through `lending.*`, inside one `db.transaction()`, and writes an audit event.
3. Never update a request's dates, title or member. Changes mean cancel + create a new request.
4. Use SQL `?` placeholders only. Never put values into SQL with f-strings.
5. Show status names exactly as the enums (`PENDING`, `RESERVED`, …) everywhere.
6. Keep code simple enough that you can explain every line.

**Git:**
- Branch `pN-<area>` (e.g. `p3-availability`). Commit small and often with clear messages.
- Edit only your files. P1 merges in the order P2 → P3 → P4 → P5/P6 → P7.
- Never commit `data/`, `.venv/` or `__pycache__/` (they are already git-ignored).

**When using AI:** review every suggestion against the rules in §2 and §3. Reject anything that adds features out of scope, changes contract files, or skips validation. Note good catches ("the AI suggested X, and we rejected it because Y"). That material is for the pitch's AI-usage section.

---

## 9. Demo data (seeded; business date 2026-08-01)
| Title | Copies | State |
|---|---|---|
| Clean Code | CC-1…CC-4 | CC-1 (asha), CC-2 (ravi) ISSUED 21 Jul → 4 Aug |
| Introduction to Algorithms | ITA-1…ITA-3 | ITA-1 (meera) RESERVED 4 → 8 Aug |
| Design Patterns | DP-1, DP-2 | DP-2 **DAMAGED** (only DP-1 can be lent) |
| Database System Concepts | DSC-1…DSC-5 | all free |
| AI: A Modern Approach | AIMA-1…AIMA-3 | AIMA-1 (kiran) ISSUED 21 Jul → 4 Aug. AIMA-2 (asha) RESERVED 6 → 7 Aug. |

**Logins:** `librarian / lib123`. Members `asha`, `ravi`, `meera`, `kiran` / `pass123`.

**Demo script:**
1. **Happy path:** asha requests *Database System Concepts* → the librarian approves → the business date moves to the start date → issue → return → the copy is free again.
2. **Conflict:** meera books *Design Patterns* (only DP-1 can be lent) for 5–10 Aug. ravi then asks for 7–8 Aug and is refused: "… already committed … next free from 11 Aug 2026". Also, asha asking for *Clean Code* 2–3 Aug is refused with `DUPLICATE_REQUEST`, because she already holds CC-1.
3. **Failure handling:** a loan is returned as DAMAGED while that copy has a future reservation. The reservation moves to another copy, or is cancelled with a reason, and the librarian sees which.
4. **Validation:** a past start date, a 31-day period, or end before start each show a clear error.

---

## 10. Glossary
| Term | Meaning here |
|---|---|
| Title | A book (e.g. *Clean Code*) |
| Copy | One physical book of a title (e.g. CC-3) |
| Request | The single record covering a booking from submission to its end |
| Commitment | An active request (PENDING / RESERVED / ISSUED) holding a copy for its dates |
| Reservation | A request in RESERVED (approved, not yet handed over) |
| Loan | A request in ISSUED (the book is with the member) |
| Business date | The simulated "today" used by every rule |
| Contract file | A shared file everyone codes against; changes need P1's approval |

**Further reading:** [README](../README.md) (setup + layout) · [Docs index](README.md) · [Business rules](03-business-rules.md) · [PRD](06-prd.md) · [Architecture](07-architecture.md) · [Edge cases](10-edge-cases.md) · [team/](team/) (your tasks)
