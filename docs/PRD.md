# Product Requirements Document: Library Management System prototype

*Draft v0.1. Assumes the BRD questions are answered as listed in BRD §5. Owner: Person 1.*

## 1. State model (single source of truth: `lms/models.py`)
```
PENDING ──approve──▶ RESERVED ──issue──▶ ISSUED ──return──▶ RETURNED
   ├──reject──▶ REJECTED      └──cancel──▶ CANCELLED
   └──cancel/withdraw──▶ CANCELLED
```
- Active statuses (these hold a copy): PENDING, RESERVED, ISSUED.
- Terminal statuses: RETURNED, REJECTED, CANCELLED. No transition leaves a terminal status.
- Copy status: IN_SERVICE, DAMAGED, UNDER_REPAIR, LOST, REFERENCE_ONLY, RESTRICTED. Only IN_SERVICE is allocatable.

## 2. Functional requirements
| ID | Requirement | Role |
|---|---|---|
| F1 | Log in with a username and password. Pages are gated by role. | All |
| F2 | Browse titles with total, in-service and free-for-period copy counts for chosen dates. | Member |
| F3 | Check availability for a title and period, with a reason when it is unavailable. | Member |
| F4 | Submit a request. The system allocates a specific free copy and the request becomes PENDING. | Member |
| F5 | View my requests with status, copy, dates, decision note and history. | Member |
| F6 | Cancel my PENDING or RESERVED request. | Member |
| F7 | Review queue: approve (→RESERVED) or reject with a mandatory reason (→REJECTED). | Librarian |
| F8 | Issue a reserved book (→ISSUED), only within [start, end]. | Librarian |
| F9 | Return a loan (→RETURNED), recording the copy condition. | Librarian |
| F10 | Change a copy's status. Show every affected commitment (moved or closed). | Librarian |
| F11 | Audit trail: every status change records who, when, from, to and a note. | System |
| F12 | Business-date override and a demo-data reset. | Demo |

## 3. Restrictions (what the system must refuse)
| Code | When | Message (example) |
|---|---|---|
| INVALID_DATES | Date missing, or end before start | "Return date must be on or after the start date." |
| START_IN_PAST | start < business today | "Start date cannot be in the past (today is 01 Aug 2026)." |
| PERIOD_TOO_LONG | More than 30 days, inclusive | "Borrowing period is 35 days; maximum is 30." |
| NO_COPY_AVAILABLE | No in-service copy free for the whole period | "All 2 in-service copies of 'Clean Code' are already committed for overlapping dates. A copy is next free from 05 Aug 2026." |
| DUPLICATE_REQUEST | Member already has an overlapping active request for the title | "You already have an active request for this title in that period." |
| INVALID_TRANSITION | Any move not allowed by the state model (e.g. approve REJECTED, cancel ISSUED, edit a rejected request) | "Cannot approve a request that is REJECTED." |
| NOT_AUTHORIZED | Wrong role, or cancelling someone else's request | "Only librarians can approve requests." |
| ISSUE_NOT_ALLOWED | Issue before the start date or after the end date | "Cannot issue before the start date (05 Aug 2026)." |
| REASON_REQUIRED | Reject with an empty reason | "A rejection reason is required." |
| LOGIN_FAILED | Bad credentials | "Invalid username or password." |

There is no edit API for requests: dates, title and member are immutable after submission.

## 4. Non-functional requirements
- **Integrity:** every write runs in one SQLite transaction (`BEGIN IMMEDIATE`). A DB trigger blocks overlapping active commitments even if the application code has a bug.
- **Usability:** every error is a plain-English `st.error` and never a stack trace. Statuses use the same names everywhere.
- **Explainability:** small modules, one owner each. The business rules live only in `availability.py` and `services.py`.
- **Portability:** Python 3.10+, `pip install -r requirements.txt`, `streamlit run app.py`. No external services.
- **Performance:** fine at hackathon scale (tens of titles, hundreds of requests). SQLite suits a mostly-read, low-concurrency workload.
- **Testability:** pytest uses a fresh, seeded temporary DB per test.

## 5. Acceptance criteria (demo scenarios)
1. **Happy path:** asha requests *Database System Concepts* 05 to 12 Aug → PENDING → librarian approves → RESERVED → business date set to 05 Aug → issue → ISSUED → return IN_SERVICE → RETURNED, and the copy is free again.
2. **Conflict:** with business date 01 Aug, *Clean Code* 02 to 03 Aug has 2 free copies. After two members book those, a third request fails with NO_COPY_AVAILABLE and the reason.
3. **Restricted copy:** *Design Patterns* only ever offers DP-1, because DP-2 is DAMAGED.
4. **Reject releases:** reject the request holding the last free copy, and a new request for the same dates succeeds.
5. **Cancel releases:** the same as 4, via cancelling a reservation.
6. **Damaged on return:** return a loan as DAMAGED while that copy has a future reservation. The reservation moves to another copy, or is cancelled with a reason, and both outcomes are shown.
7. **Invalid input:** a past start date, a 31-day period, or end before start each show a clear error and create no request.
