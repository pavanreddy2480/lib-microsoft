# 07 · Architecture

> **Stage:** Design · **Owner:** P7 (maintains), whole team (explains)
> **Prev:** [06 · PRD](06-prd.md) · **Next:** [08 · Code Structure](08-code-structure.md)

**TL;DR:** a single-process **Streamlit** app over a local **SQLite** file. The code is layered **UI → services → persistence → domain**. One `requests` table plus one **state machine** covers request, reservation and loan. Availability is **computed per physical copy**, never stored. Double booking is prevented **twice**: by the service check inside a locked transaction, and by a **database trigger**.

---

## 1. Architectural drivers
What the design optimises for, in priority order. When two goals conflict, the higher one wins.
```
 1. CORRECTNESS of copy commitments   (never double-book: the core business risk)
 2. EXPLAINABILITY                    (every member must explain their part)
 3. DELIVERY SPEED                    (90 minutes, 7 people working in parallel)
 4. CLEAR FEEDBACK                    (every refusal says why)
 5. PERFORMANCE / SCALE               (tiny data; deliberately last)
```

## 2. System context (who talks to what)
```
      +----------+                                  +-------------+
      |  Member  |                                  |  Librarian  |
      | (browser)|                                  |  (browser)  |
      +----+-----+                                  +------+------+
           |   request, track, cancel                      |  review, issue, return,
           |                                               |  manage copies
           v                                               v
      +---------------------------------------------------------------+
      |            Library Management System (this repo)              |
      |   Streamlit app  +  lms package  +  SQLite file (data/)       |
      +---------------------------------------------------------------+

      No external systems: no cloud, no email, no APIs (hackathon constraint).
```

## 3. Runtime / deployment view
```
  Laptop (Windows / macOS / Linux, Python 3.10+)
  +--------------------------------------------------------------------+
  |  python -m streamlit run app/Home.py                               |
  |                                                                    |
  |  +----------------------------+        +-----------------------+   |
  |  | Streamlit server :8501     |  sql   | data/library.db       |   |
  |  |  - one Python process      |------->| (SQLite file, created |   |
  |  |  - reruns page script on   |        |  + seeded on first    |   |
  |  |    every interaction       |        |  start)               |   |
  |  |  - session_state = login   |        +-----------------------+   |
  |  +-------------^--------------+                                    |
  +----------------|---------------------------------------------------+
                   | http://localhost:8501
            +------+------+
            |   Browser   |   (member and librarian can use separate tabs)
            +-------------+
```
- **Session state** (per browser tab): the logged-in `User`.
- **Process state** (shared by all tabs): the business date (`clock.py`). This is a known limitation, W4 in [05](05-critique-and-open-questions.md).
- **Durable state**: only the SQLite file.

## 4. Layered architecture
```
 +--------------------------------------------------------------------------+
 | PRESENTATION    app/Home.py, app/pages/*.py                              |
 |                 Draw widgets, call services, show results. NO rules.     |
 +--------------------------------------------------------------------------+
 | UI SUPPORT      lms.ui.common                                            |
 |                 page_setup (login + role guard), run_action (errors),    |
 |                 sidebar (user, business date, logout)                    |
 +--------------------------------------------------------------------------+
 | SERVICES        lms.services                                             |
 |   auth          login, require_role                                      |
 |   availability  copy-level availability engine (pure-ish logic)          |
 |   lending       state machine: submit/approve/reject/cancel/issue/return |
 |                 + copy status changes + reallocation policy              |
 +--------------------------------------------------------------------------+
 | PERSISTENCE     lms.persistence                                          |
 |   db            connection, transaction() = BEGIN IMMEDIATE..COMMIT      |
 |   repository    SQL <-> dataclasses (no business rules)                  |
 |   schema.sql    tables, CHECKs, FKs, no-overlap TRIGGERS                 |
 |   seed          PDF initial data, reset                                  |
 +--------------------------------------------------------------------------+
 | DOMAIN          lms.domain   (pure Python, no I/O, no imports from above)|
 |   models        enums, ALLOWED_TRANSITIONS, dataclasses                  |
 |   errors        BusinessRuleError + codes                                |
 |   clock         business_today()                                         |
 |   security      hash_password()                                          |
 +--------------------------------------------------------------------------+
   lms.config: every file-system path (DB, schema, data dir), used by persistence
```

### 4.1 Dependency rule (arrows = "imports")
```
   app/pages ---> lms.ui.common ---+
       |                           |
       +------------+--------------+
                    v
             lms.services.lending ---> lms.services.availability
                    |       \                  |
                    |        +--> lms.services.auth
                    v                          v
             lms.persistence.db / repository  <-------+
                    |                                 |
                    v                                 |
               lms.domain  <-- everyone may import ---+
               lms.config

   FORBIDDEN: domain -> anything above it
              persistence -> services / ui
              services -> ui
              anything in src/lms except lms.ui -> streamlit
```
This was verified by grep during the restructure; it's in [12 · Iteration Log](12-iteration-log.md).

## 5. Data model
```
 +---------------+          +---------------+  1      *  +----------------+
 | users         |          | titles        |------------| copies         |
 |---------------|          |---------------|            |----------------|
 | id         PK |          | id         PK |            | id          PK |
 | username   UQ |          | title      UQ |            | title_id    FK |
 | password_hash |          | category      |            | copy_code   UQ |
 | full_name     |          +-------+-------+            | status  CHECK  |
 | role   CHECK  |                  | 1                  | note           |
 +-------+-------+                  |                    +-------+--------+
         | 1                        | *                          | 1
         |              +-----------+-----------+                |
         +------------* | requests              | *--------------+
                        |-----------------------|
                        | id                 PK |
                        | member_id   FK users  |
                        | title_id    FK titles |
                        | copy_id     FK copies |   <- the committed copy
                        | start_date, end_date  |   CHECK end >= start
                        | status        CHECK   |
                        | created_at            |
                        | decision_note         |
                        | issued_at, returned_at|
                        +-----------+-----------+
                                    | 1
                                    | *
                        +-----------+-----------+
                        | request_events        |   append-only audit trail
                        |-----------------------|
                        | id, request_id FK     |
                        | from_status, to_status|
                        | actor, note, at       |
                        +-----------------------+

 Indexes: requests(copy_id, status), requests(member_id, status)
 Triggers: trg_no_overlap_insert, trg_no_overlap_update  (IR1)
```
**Why `requests.title_id` *and* `copy_id`?** The member asks for a **title**, and the system commits a **copy**. Keeping both lets us re-allocate a copy (PR6) without losing what the member asked for.

## 6. State machines
### 6.1 Request
```
                         submit (copy allocated)
                                  |
                                  v
                            +-----------+
               +------------|  PENDING  |------------+
               | reject     +-----------+   cancel   |
               | (reason)         | approve          | (owner/librarian)
               v                  v                  v
        +------------+     +-----------+      +-------------+
        |  REJECTED  |     | RESERVED  |----->|  CANCELLED  |
        +------------+     +-----------+cancel+-------------+
                                 | issue (start <= today <= end)
                                 v
                           +-----------+
                           |  ISSUED   |
                           +-----------+
                                 | return (+ copy condition)
                                 v
                           +-----------+
                           | RETURNED  |
                           +-----------+
        [ ACTIVE = PENDING, RESERVED, ISSUED ]   [ TERMINAL = the other three ]
```
### 6.2 Copy
```
               mark damaged / repair / lost / reference / restricted
   +------------+ ---------------------------------------------> +----------------+
   | IN_SERVICE |                                                | DAMAGED        |
   | (lendable) | <--------------------------------------------- | UNDER_REPAIR   |
   +------------+               mark IN_SERVICE                  | LOST           |
         ^                                                       | REFERENCE_ONLY |
         |  return with condition = IN_SERVICE                   | RESTRICTED     |
         +---- (return with any other condition -> right side) --+----------------+
   Leaving IN_SERVICE triggers the reallocation policy (PR6) for future bookings.
```

## 7. Key flows
### 7.1 Submit a request (BR1, BR4, BR6, BR10, PR1, PR2)
```
 Member   Catalog page   ui.common      lending           availability      repository      SQLite
   |  Submit   |             |              |                    |                |             |
   |---------->| run_action  |              |                    |                |             |
   |           |------------>| submit_request(actor,title,s,e)   |                |             |
   |           |             |------------->| require MEMBER     |                |             |
   |           |             |              | validate_period -->|                |             |
   |           |             |              |<----- ok / raise --|                |             |
   |           |             |              | BEGIN IMMEDIATE ------------------------------------>| (write lock)
   |           |             |              | duplicate check --------------------------->|      |
   |           |             |              | find_free_copy --->| list copies + commitments ->|   |
   |           |             |              |<---- copy | None --|                |             |
   |           |             |              |   None -> raise NO_COPY_AVAILABLE(reason) -> ROLLBACK
   |           |             |              | insert PENDING ---------------------------->|----->| trigger IR1
   |           |             |              | insert event ------------------------------>|----->|
   |           |             |              | COMMIT ------------------------------------------------>|
   |           |             |<-- Request --|                    |                |             |
   |           |<- success --|              |                    |                |             |
   |<- "Request #7 PENDING" -|              |                    |                |             |
```

### 7.2 Return as damaged, with reallocation (BR9, PR6)
```
 Librarian -> return_loan(actor, req#1, condition=DAMAGED)
   BEGIN IMMEDIATE
     req#1: ISSUED -> RETURNED, returned_at=now, event
     copy CC-3.status = DAMAGED
     for each future PENDING/RESERVED on CC-3:          e.g. req#9 RESERVED 10-12 Aug
         free = find_free_copy(title, 10-12, exclude=req#9)
         free?  yes -> req#9.copy_id = CC-4, event "moved CC-3 -> CC-4"    => MOVED
                no  -> req#9 -> CANCELLED, note "copy became unavailable"  => CLOSED
   COMMIT
 <- (request, [AffectedRequest(req#9, MOVED, CC-3 -> CC-4)])  -> UI shows st.info / st.warning
```

### 7.3 Error path (BR10)
```
 service raises BusinessRuleError(code, message)
      -> transaction() ROLLBACK   (nothing half-written)
      -> run_action() catches it  -> st.error(message)  -> returns None
      -> page shows the message; no stack trace; state unchanged
```

## 8. Availability algorithm (BR2-BR5, PR5)
```python
def is_copy_free(copy, start, end, today, exclude_id=None):
    if copy.status != IN_SERVICE:                      # BR5
        return False
    for r in active_commitments_for_copy(copy.id):    # PENDING / RESERVED / ISSUED
        if r.id == exclude_id:
            continue
        r_end = max(r.end_date, today) if r.status == ISSUED else r.end_date   # PR5 overdue
        if r.start_date <= end and start <= r_end:     # inclusive overlap (BR3, A2)
            return False
    return True

find_free_copy = first copy (ordered by copy_code) where is_copy_free(...)   # PR11
```
Cost: O(copies × commitments per copy). That's trivial at library scale.

## 9. Integrity & concurrency: defence in depth for BR3
```
   request to commit copy C for [s, e]
              |
   +----------v-----------+   Layer 1: SERVICE CHECK
   | find_free_copy()     |   - knows business context (status, overdue, exclusions)
   | inside BEGIN         |   - gives the friendly reason message
   | IMMEDIATE (write lock)|  - write lock: no other writer can slip in between
   +----------+-----------+     "check" and "insert"
              |
   +----------v-----------+   Layer 2: DATABASE TRIGGER (IR1)
   | trg_no_overlap_*     |   - last line of defence against bugs in ANY code path
   | RAISE(ABORT,         |   - tested: overlap blocked, adjacent dates allowed,
   |  'COPY_OVERLAP')     |     re-activating an overlapping row blocked
   +----------+-----------+
              v
         row committed
```
- **Atomicity:** every service call is one transaction. Status change, copy change and audit event all commit together, or none of them do.
- **Concurrency model:** SQLite allows a single writer at a time. `BEGIN IMMEDIATE` serialises writes, and reads never block. That is ample for one library desk.

## 10. Configuration & paths
```
 src/lms/config.py
   PACKAGE_DIR  = <root>/src/lms                (from __file__, not the CWD)
   PROJECT_ROOT = <root>
   DATA_DIR     = $LMS_DATA_DIR  or <root>/data
   DB_PATH      = $LMS_DB_PATH   or DATA_DIR/library.db
   SCHEMA_PATH  = PACKAGE_DIR/persistence/schema.sql
 Tests call db.set_db_path(tmp_path/"test.db"), so every test gets an isolated DB.
```

## 11. Security model (prototype)
| Aspect | Prototype | Production |
|---|---|---|
| Authentication | Username + password, `sha256(static salt + pw)` | SSO (university IdP), bcrypt/argon2 |
| Authorisation | Role check in **services** (`require_role`) + ownership check; the UI also hides pages | The same, plus API-level enforcement |
| Session | Streamlit `session_state` per tab | Signed session or token, with expiry |
| SQL injection | Parameterised queries only (`?`) | Same |
| Audit | `request_events` | Plus central log retention |
Authorisation is enforced in the **service layer**, not just the UI. A page that forgot its role guard still can't approve a request.

## 12. Trade-offs (decision records)
| # | Decision | Alternatives considered | Why we chose it | What it costs us |
|---|---|---|---|---|
| T1 | **SQLite** | PostgreSQL, JSON/CSV, in-memory | Mostly reads, a single desk, zero setup. Transactions, constraints and triggers. Postgres wasn't installed. | One writer at a time. No range-exclusion constraint (we use a trigger instead). |
| T2 | **Streamlit** | Flask/FastAPI + HTML/React | One language, fast UI, everyone can read it | Rerun model quirks. Limited layout control. Not multi-tenant. |
| T3 | **One `requests` entity + state machine** | Separate Request / Reservation / Loan tables | One place to check overlaps. No copying rows between tables. Simple audit. | Some columns only matter in some states (`issued_at`) |
| T4 | **Computed availability** | A stored "available" flag or counter per title or copy | Can never drift out of sync. Releasing a copy is automatic. | A query per check (negligible at this scale) |
| T5 | **Allocate the copy at submission** | Allocate at approval or at issue | Matches BR3/BR7. The member knows immediately. | Pending requests hold copies (W1) |
| T6 | **App check + DB trigger** | App check only | Defence in depth. Bugs in one path can't double-book. | Overlap logic exists in two places (Python + SQL) |
| T7 | **First-fit allocation** | Best-fit, or re-shuffling existing bookings | Deterministic and explainable. Never moves bookings silently. | Occasionally refuses a request a reshuffle could fit (W2) |
| T8 | **Business date (configurable)** | The real clock, or shifting the seed data | Keeps the PDF data meaningful. Demo can "time travel". | Global to the process (W4) |
| T9 | **Simple login** | No auth, a role dropdown, SSO | Real identity for ownership and librarian-only rules | Demo-grade hashing (W5) |
| T10 | **Move-or-close on copy loss** | Block the status change, or just flag it | No silent overwrite, and members keep bookings where possible | More logic in `lending.py` |
| T11 | **Immutable requests** | Allow editing dates | Matches BR7. History stays truthful. Simpler overlap logic. | A member must cancel and re-request to change dates |
| T12 | **Layered `src/` package + contract-first stubs** | Flat scripts; everyone codes freely | 7 people work in parallel without conflicts. Clear ownership. | About 15 minutes of upfront design |
| T13 | **Inclusive dates** | Exclusive end | Matches how people say "until 4 Aug" | A copy can't turn around on the same day |
| T14 | **Audit events table** | No history | Visibility (P3), debuggability, demo value | An extra insert per action |

## 13. Known limitations
- Single process, single machine. The business date is shared by all users (W4).
- Demo-grade authentication (W5). No notifications (W7).
- First-fit allocation (W2). Overdue loans only block up to today (W3).
- No pagination or search. Fine for the 5 seeded titles; it would need work for a real catalogue.

## 14. Evolution path (what changes for production)
```
  PROTOTYPE (today)                         PRODUCTION (next)
  -----------------                         -----------------
  Streamlit pages          ---------->      Web UI (React) + REST API (FastAPI)
  lms.services (Python)    ---------->      unchanged: the same services behind the API
  SQLite + trigger         ---------->      PostgreSQL + EXCLUDE USING gist
                                            (copy_id WITH =, daterange WITH &&)
  sha256 login             ---------->      University SSO (OIDC)
  business date            ---------->      real clock + scheduled jobs (overdue, expiry)
  (none)                   ---------->      notification worker (email / in-app)
  single laptop            ---------->      container + managed DB, backups
```
Because the business rules sit in `lms.services` and depend only on the repository functions, the core logic **survives** the move. Only the edges change.
