# 06 · Product Requirements (PRD)

> **Stage:** Specify · **Owner:** P1 · Assumes the questions in [05](05-critique-and-open-questions.md) are answered as decided there.
> **Prev:** [05 · Critique](05-critique-and-open-questions.md) · **Next:** [07 · Architecture](07-architecture.md)

This document says **what** the product does, what it **refuses** to do, and **how well** it must do it. Business rule IDs (BR, PR, IR) refer to [03](03-business-rules.md).

---

## 1. State model (single source of truth: `src/lms/domain/models.py`)
```
 PENDING --approve--> RESERVED --issue--> ISSUED --return--> RETURNED
    |                    |
    +--reject--> REJECTED +--cancel--> CANCELLED
    +--cancel/withdraw--> CANCELLED
```
- **Active statuses** (hold a copy): PENDING, RESERVED, ISSUED
- **Terminal statuses**: RETURNED, REJECTED, CANCELLED. No transition leaves them.
- **Copy status**: IN_SERVICE, DAMAGED, UNDER_REPAIR, LOST, REFERENCE_ONLY, RESTRICTED. Only IN_SERVICE is allocatable.

## 2. Functional requirements
| ID | Requirement | Role | Priority | Rules |
|---|---|---|---|---|
| F1 | Log in with a username and password. Pages are gated by role. | All | Must | A11 |
| F2 | Browse titles with total, in-service and free-for-period copy counts for chosen dates | Member | Must | BR2 |
| F3 | Check availability for a title and period, with a reason when it is unavailable | Member | Must | BR4, BR10 |
| F4 | Submit a request. The system allocates a specific free copy and the request becomes PENDING. | Member | Must | BR1, BR4, BR6 |
| F5 | View my requests with status, copy, dates, decision note and history | Member | Must | P3 |
| F6 | Cancel my PENDING or RESERVED request | Member | Must | BR8 |
| F7 | Review queue: approve (→ RESERVED) or reject with a mandatory reason (→ REJECTED) | Librarian | Must | BR6, BR7, PR7 |
| F8 | Issue a reserved book (→ ISSUED), only within [start, end] | Librarian | Must | PR4 |
| F9 | Return a loan (→ RETURNED), recording the copy's condition | Librarian | Must | BR9 |
| F10 | Change a copy's status; show every affected booking (moved or closed) | Librarian | Should | BR5, PR6 |
| F11 | Audit trail: every change records who, when, from, to and a note | System | Should | PR10 |
| F12 | Business-date override in the sidebar, plus a demo-data reset | Demo | Must | PR12 |
| F13 | Bonus: dashboard of overdue / due-soon loans and utilisation | Librarian | Could | - |

## 3. Restrictions (what the system must refuse)
| Code | When | Message (example) |
|---|---|---|
| `INVALID_DATES` | A date is missing, or end is before start | "Return date must be on or after the start date." |
| `START_IN_PAST` | start < business date | "Start date cannot be in the past (today is 01 Aug 2026)." |
| `PERIOD_TOO_LONG` | More than 30 days, inclusive | "Borrowing period is 35 days; maximum is 30." |
| `NO_COPY_AVAILABLE` | No in-service copy is free for the whole period | "All 2 in-service copies of 'Clean Code' are already committed for overlapping dates. A copy is next free from 05 Aug 2026." |
| `DUPLICATE_REQUEST` | The member already has an overlapping active request for this title | "You already have an active request for this title in that period." |
| `INVALID_TRANSITION` | Any move not allowed by §1 (e.g. approving a REJECTED request, cancelling an ISSUED one) | "Cannot approve a request that is REJECTED." |
| `NOT_AUTHORIZED` | Wrong role, or cancelling someone else's request | "This action requires the LIBRARIAN role." |
| `ISSUE_NOT_ALLOWED` | Issue before the start date or after the end date | "Cannot issue before the start date (05 Aug 2026)." |
| `REASON_REQUIRED` | Reject with an empty reason | "A rejection reason is required." |
| `LOGIN_FAILED` | Bad credentials | "Invalid username or password." |
| `NOT_FOUND` | Unknown request or copy id | "Request #42 not found." |

**There is no edit API for requests.** Dates, title and member are immutable after submission (PR9).

## 4. Non-functional requirements
| Quality | Requirement | How it's met |
|---|---|---|
| **Integrity** | No copy is ever double-booked; no half-applied action | One `BEGIN IMMEDIATE` transaction per action, plus the DB trigger (IR1) |
| **Usability** | Every refusal is a plain-English message, never a stack trace. Statuses are named the same everywhere. | `run_action` → `st.error`, plus the enums |
| **Explainability** | Any member can explain any rule's location | Layered code; rules live only in `services/` |
| **Traceability** | Every change is attributable | `request_events` audit table |
| **Portability** | Runs on any laptop with Python 3.10+, offline | `pip install -r requirements.txt`; SQLite file. No external services. |
| **Performance** | Interactive (< 1 s per action) at tens of titles and hundreds of requests | SQLite with indexes on `(copy_id, status)` |
| **Testability** | Rules are testable without the UI | pytest with a fresh seeded DB per test |
| **Maintainability** | Change a rule in one place | One source of truth: `ALLOWED_TRANSITIONS`, `config.py`, `clock.py` |

## 5. Acceptance criteria (demo scenarios)
1. **Happy path:** asha requests *Database System Concepts* 05 → 12 Aug → PENDING → the librarian approves → RESERVED → the business date moves to 05 Aug → issue → ISSUED → return IN_SERVICE → RETURNED. The copy is free again.
2. **Conflict:** with the business date at 01 Aug, meera books *Design Patterns* 05 → 10 Aug, taking DP-1, the only lendable copy. ravi's request for 07 → 08 Aug fails with `NO_COPY_AVAILABLE`: "… already committed for overlapping dates. A copy is next free from 11 Aug 2026." Separately, asha requesting *Clean Code* 02 → 03 Aug fails with `DUPLICATE_REQUEST`, because she already holds CC-1 for those dates.
3. **Restricted copy:** *Design Patterns* only ever offers DP-1, because DP-2 is DAMAGED.
4. **Reject releases:** reject the request holding the last free copy. A new request for the same dates then succeeds.
5. **Cancel releases:** the same as 4, via cancelling a reservation.
6. **Damaged on return:** return a loan as DAMAGED while that copy has a future reservation. The reservation moves to another copy, or is cancelled with a reason, and the outcome is shown.
7. **Invalid input:** a past start date, a 31-day period, or end before start each show a clear error and create no request.

## 6. User stories
| ID | As a… | I want to… | So that… | Acceptance |
|---|---|---|---|---|
| US1 | member | see which titles have a free copy for my dates | I only request what I can actually get | F2: counts match per-copy availability |
| US2 | member | be told exactly why I can't request a title | I can pick other dates | F3: reason names the cause + next free date |
| US3 | member | track my request status and history | I don't have to ask the librarian | F5 |
| US4 | member | cancel a booking I no longer need | the copy goes to someone else | F6: free count goes back up |
| US5 | librarian | see all pending requests in one queue | I can review them quickly and fairly | F7 |
| US6 | librarian | reject with a reason | the member understands the decision | PR7 |
| US7 | librarian | record that a returned book is damaged | it isn't lent again until repaired | F9 + BR5 |
| US8 | librarian | know which bookings are affected when a copy breaks | nobody is silently let down | F10 + PR6 |

## 7. Screens (wireframes)
| Page | File | Role | Owner |
|---|---|---|---|
| Home / Login | `app/Home.py` | all | P1 |
| Catalog | `app/pages/1_Catalog.py` | member | P5 |
| My Requests | `app/pages/2_My_Requests.py` | member | P5 |
| Review Queue | `app/pages/3_Review_Queue.py` | librarian | P6 |
| Loans | `app/pages/4_Loans.py` | librarian | P6 |
| Inventory | `app/pages/5_Inventory.py` | librarian | P6 |

```
 +-- Catalog ---------------------------------------------------------------+
 | Start [01 Aug 2026]   Return by [14 Aug 2026]                            |
 |                                                                          |
 | Title                      Category   Total  In service  Free  Note      |
 | Clean Code                 SW Eng       4        4         2   ...       |
 | Design Patterns            SW Design    2        1         1             |
 | ...                                                                      |
 |                                                                          |
 | Request a book: [ Clean Code        v]  [Check availability]             |
 |   (green) 2 copies free for 01-14 Aug          [Submit request]          |
 |   (red)   All 2 in-service copies ... next free from 05 Aug 2026         |
 +--------------------------------------------------------------------------+

 +-- Review Queue (librarian) ----------------------------------------------+
 | #7  asha  Database System Concepts  copy DSC-1  05-12 Aug  (10:41)       |
 |     note [____________]  [Approve]     reason [____________]  [Reject]   |
 | #8  kiran Clean Code                copy CC-3   02-03 Aug  (10:44)       |
 |     note [____________]  [Approve]     reason [____________]  [Reject]   |
 +--------------------------------------------------------------------------+

 +-- Loans (librarian) -----------------------------------------------------+
 | [Confirmed reservations] [Active loans] [All requests]                   |
 | #3 meera  Intro to Algorithms  ITA-1  04-08 Aug        [Issue] [Cancel]  |
 | #1 asha   Clean Code  CC-1  due 04 Aug  OVERDUE                          |
 |     condition [IN_SERVICE v]  note [______]                [Return]      |
 +--------------------------------------------------------------------------+
```
Sidebar on every page: the logged-in user, **Business date** picker, and **Log out**.
