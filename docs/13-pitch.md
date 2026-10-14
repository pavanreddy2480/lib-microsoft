# 13 · Pitch (2 slides + demo script)

> **Stage:** Present · **Owner:** P1
> **Prev:** [12 · Iteration Log](12-iteration-log.md) · **Index:** [docs/README.md](README.md)

Two slides, then a live demo of about 4 minutes. Each slide has speaker notes. Every team member should be able to answer the questions at the bottom.

---

## Slide 1 · Problem Understanding

**The problem.** A university library runs requests, reservations, loans and returns on registers and spreadsheets. As a result, copies get promised twice, students request books without checking availability, nobody can see a request's status, cancelled or returned copies stay "unavailable", and damaged copies aren't tracked. ([01](01-problem-statement.md))

**Who it's for** ([02](02-stakeholders-and-workflows.md))
| Persona | Needs |
|---|---|
| **Member** (student or researcher) | See what is free for *my dates*, request it, track it, cancel it |
| **Librarian** | One review queue; issue, take returns, record damage |
| Library head | Inventory health (only partly in scope) |

**Workflows, in priority order**
1. Request → review → confirmed reservation → loan → return *(the core)*
2. Reject with a reason · 3. Cancel before issue · 4. Return damaged · 5. Change a copy's status

**The rules that shape the design** ([03](03-business-rules.md))
- **BR3, no overlap:** a physical copy never has two overlapping active commitments.
- **BR4, whole period:** refused *before* submission unless one copy is free for the **entire** period. No partial fulfilment and no alternatives.
- **BR7, reject releases:** rejection closes the request and frees the copy. It is never edited; the member makes a new request.

**Key assumptions** ([04](04-assumptions-and-scope.md))
A1, the copy is committed at submission · A2, dates are inclusive · A3, the business date is 01 Aug 2026 · A4, a period is at most 30 days · A8, a damaged copy's bookings are moved or closed, never silently · A11, simple login

**90-minute scope:** both roles, login, copy-level availability, the full lifecycle, inventory status, an audit trail, seeded PDF data and tests.
*Out:* fines, renewals, waitlists, notifications, SSO, multiple branches.

> **Speaker notes.** The root cause is that nobody records *which copy* is promised *when*. Our whole design follows from making that one fact explicit. A1 is the key interpretation: the PDF says rejection "releases" a copy, so a pending request must already hold one.

---

## Slide 2 · Solution & Engineering Decisions

**Stack:** Python + **Streamlit** (UI) + **SQLite** (stdlib). One `pip install`, runs on a laptop, and needs no services.

**Design decisions**
| Decision | Why |
|---|---|
| **One request entity, one state machine.** `PENDING → RESERVED → ISSUED → RETURNED`, plus `REJECTED` / `CANCELLED`. | A request never changes into a different object, so there is one history and one place for rules. Legal moves live only in `ALLOWED_TRANSITIONS`. |
| **Availability is computed, not stored.** A copy is free if it is `IN_SERVICE` and no active request overlaps. | No "available" flag to forget to reset. Cancel, reject and return free the copy automatically (BR7–BR9). |
| **Two safety layers for BR3.** The service checks inside `BEGIN IMMEDIATE`, and a **SQLite trigger** rejects any overlapping row. | Even a bug in our Python code can't double-book a copy. |
| **Layered code:** pages → services → repository → domain | Business rules live only in `services/`. Pages just call them and show `st.error(reason)`. |

**Trade-offs we accept** ([05](05-critique-and-open-questions.md))
- Pending requests hold copies, so unreviewed requests can block others (production fix: auto-expiry).
- First-fit allocation is deterministic and explainable but not always optimal.
- The business date is global to the running app, and login is demo-grade (static salt).

**How we tested** ([11](11-test-evidence.md))
- We wrote pytest tests *before* the code, against the contract (TDD), with a fresh seeded DB per test.
- A trigger test inserts an overlapping row directly. It proves BR3 holds below the application layer.
- Every BR1–BR10 rule maps to at least one test. The demo scenarios below were also run by hand.

**AI usage:** AI drafted code and docs, and we checked every output against the rules. *Example:* reviewing the demo script showed that the planned *Clean Code* conflict would hit `DUPLICATE_REQUEST` (both remaining members already hold Clean Code loans), not `NO_COPY_AVAILABLE`. We moved the conflict demo to *Design Patterns*.

**Limitations and next steps:** no notifications, renewals or fines; demo-grade auth; one library branch. Next: auto-expire pending requests, email notifications, SSO, Postgres with an exclusion constraint.

> **Speaker notes.** If asked "why not a status flag on the copy?", the answer is that time-based availability is a *query* over requests. Copy status only describes physical condition. If asked "why SQLite?", it's a low-concurrency, mostly-read workload, and `BEGIN IMMEDIATE` serialises writers.

---

## Demo script (≈ 4 min)

**Setup:** `python -m streamlit run app/Home.py`. Before each scenario, log in as `librarian`, open **Inventory**, and click **Reset demo data**. This also sets the business date back to **01 Aug 2026**.

### 1 · Happy path (BR6, BR9)
1. Log in as **asha / pass123** → **Catalog**, dates **05 → 12 Aug**. *Database System Concepts* shows 5 of 5 copies free.
2. Submit a request → "Request #… submitted (PENDING)". **My Requests** shows it PENDING on copy DSC-1.
3. Log out, then log in as **librarian / lib123** → **Review Queue** → **Approve** → RESERVED.
4. In the sidebar, set the business date to **05 Aug** → **Loans** → **Issue** → ISSUED.
5. **Return** with condition **IN_SERVICE** → RETURNED. The Catalog shows 5 of 5 free again: the copy was released automatically.
6. *Optional:* open the request's **History** to show the audit trail (who, when, from → to).

### 2 · Conflict and validation (BR3, BR4, BR7, BR10)
1. Log in as **meera** → request *Design Patterns* **05 → 10 Aug**. She gets **DP-1**, the only lendable copy, because DP-2 is DAMAGED (BR5).
2. Log in as **ravi** → request *Design Patterns* **07 → 08 Aug** → refused: *"All 1 in-service copies of 'Design Patterns' are already committed for overlapping dates. A copy is next free from 11 Aug 2026."* No request is created.
3. Still as ravi, try **01 → 31 Aug** → *PERIOD_TOO_LONG*, and **03 → 02 Aug** → *INVALID_DATES*. Each shows a clear message.
4. Log in as **librarian** → **Review Queue** → **Reject** meera's request. A reason is required, so first show that an empty reason is refused.
5. Log in as **ravi** again → **07 → 08 Aug** now succeeds on DP-1. Rejection released the copy (BR7).

### 3 · Damaged on return (BR9, A8)
1. Log in as **asha** → request *AI: A Modern Approach* **10 → 12 Aug**. She gets **AIMA-1**, the copy kiran has on loan until 04 Aug.
2. Log in as **librarian** → **Approve** (RESERVED).
3. Set the business date to **03 Aug** → **Loans** → return kiran's AIMA-1 loan with condition **DAMAGED**.
4. A warning appears: asha's reservation was **MOVED** from AIMA-1 to AIMA-2, and AIMA-1 is no longer lent out. Nothing changed silently, and the move is in the request's history.
5. *Optional, the CLOSED outcome:* asha requests *Design Patterns* → **Inventory** → set DP-1 to **UNDER_REPAIR** → her request is REJECTED: *"Copy DP-1 became unavailable and no other copy is free for these dates."*

> **Why not the *Clean Code* conflict from the PRD?** Its two free copies would go to meera and kiran. The only members left, asha and ravi, already hold Clean Code loans over those dates, so they would correctly get `DUPLICATE_REQUEST` instead of `NO_COPY_AVAILABLE`. *Design Patterns* shows the conflict with one copy and also shows BR5.

---

## Questions to be ready for
| Question | Short answer | Who |
|---|---|---|
| Why must every request be reviewed (BR6)? | Library control over scarce copies. Submit only ever creates PENDING; approve and reject are librarian-only and enforced in the service, not just hidden in the UI. | P1, P4 |
| Why a simple login (A11)? | Without identity, "only librarians approve" and "only the owner cancels" would be a dropdown anyone could change. It is demo-grade on purpose and documented as a limitation. | P1, P2 |
| How do you *know* a copy is never double-booked? | Two layers, the service check and the DB trigger, and a test that bypasses the app to prove the trigger works. | P3, P7 |
| What happens to bookings when a copy is damaged? | Moved to another free copy, otherwise closed with a reason. The librarian always sees the list. | P4, P6 |
