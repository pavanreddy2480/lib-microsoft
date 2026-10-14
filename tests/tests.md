# Library Management System — Required Test Suite

This checklist follows `docs/team/7.md`, `docs/team/3.md`, `docs/PRD.md`, and the service contracts. Check a box only after running and verifying the case. This file specifies tests; it does not claim they have passed.

## Setup and conventions

- Run commands from the project root.
- Use the existing fixtures in `tests/conftest.py`: `conn`, `librarian`, `asha`, `ravi`, and `title_id`.
- Each test receives a fresh seeded SQLite database and business date **2026-08-01**. Use the business clock rather than the real current date.
- All dates below refer to August 2026 unless stated otherwise. Date ranges are inclusive.
- Assert `BusinessRuleError.code` and the contract message where specified.
- For failed writes, also assert no unwanted changes to requests, copy assignments, copy status, or audit history.
- Initial `NotImplementedError` failures are expected while service implementations are pending. Report failing test names to the relevant owner; do not change application code as part of this testing assignment.

## 1. Availability — `tests/test_availability.py`

### Date overlap and period validation

| Done | ID | Case | Expected result |
|---|---|---|---|
| [ ] | AV01 | Partially overlapping periods | `overlaps` returns `True` |
| [ ] | AV02 | One period contains another | `True` |
| [ ] | AV03 | Identical periods | `True` |
| [ ] | AV04 | One period ends on the other period's start date | `True`; touching dates overlap |
| [ ] | AV05 | One period ends the day before another starts | `False` |
| [ ] | AV06 | Disjoint periods, in either argument order | `False` |
| [ ] | AV07 | Same-day borrowing | Valid; inclusive duration is one day |
| [ ] | AV08 | Missing start, missing end, or both missing | `INVALID_DATES`: `Please choose both a start and a return date.` |
| [ ] | AV09 | End before start | `INVALID_DATES`: `Return date must be on or after the start date.` |
| [ ] | AV10 | Start before business today | `START_IN_PAST`; message includes formatted business date |
| [ ] | AV11 | Start equals business today | Valid |
| [ ] | AV12 | Exactly 30 days inclusive, e.g. 01–30 Aug | Valid |
| [ ] | AV13 | 31 days inclusive, e.g. 01–31 Aug | `PERIOD_TOO_LONG`: `Borrowing period is 31 days; maximum is 30.` |
| [ ] | AV14 | Multiple validation problems | Errors checked in order: missing dates, end before start, start in past, excessive duration |

### Seeded availability expectations

Assert all three counts, not just whether the title is available.

| Done | ID | Title | Period | Business date | Free / in service / total |
|---|---|---|---|---|---|
| [ ] | AV15 | Clean Code | 02–03 Aug | 01 Aug | 2 / 4 / 4 |
| [ ] | AV16 | Clean Code | 05–06 Aug | 01 Aug | 4 / 4 / 4 |
| [ ] | AV17 | Introduction to Algorithms | 05–07 Aug | 01 Aug | 2 / 3 / 3 |
| [ ] | AV18 | Design Patterns | A valid period | 01 Aug | 1 / 1 / 2 |
| [ ] | AV19 | Artificial Intelligence: A Modern Approach (AIMA) | 06 Aug only | 01 Aug | 2 / 3 / 3 |
| [ ] | AV20 | Clean Code | 10–11 Aug | 10 Aug | 2 / 4 / 4; overdue CC-1 and CC-2 still block |

### Copy-level rules and explanations

| Done | ID | Case | Expected result |
|---|---|---|---|
| [ ] | AV21 | Copy is `IN_SERVICE` and has no overlapping commitment | Allocatable |
| [ ] | AV22 | Copy is `DAMAGED`, `UNDER_REPAIR`, `LOST`, `REFERENCE_ONLY`, or `RESTRICTED` | Never allocatable; parameterize all five statuses |
| [ ] | AV23 | Overlapping `PENDING`, `RESERVED`, or `ISSUED` request | Copy blocked; parameterize all three active statuses |
| [ ] | AV24 | `REJECTED`, `CANCELLED`, or `RETURNED` request | Its commitment does not block the copy |
| [ ] | AV25 | Issued loan before its due date | `effective_end` equals its end date |
| [ ] | AV26 | Issued loan is overdue | `effective_end` equals business today |
| [ ] | AV27 | Non-issued request | `effective_end` remains its end date |
| [ ] | AV28 | Exclude the current request ID while checking its copy | Its own commitment is ignored; other commitments still block |
| [ ] | AV29 | Multiple free copies | Sorted by `copy_code`; `find_free_copy` chooses the lowest code |
| [ ] | AV30 | No free copy | `free_copies` returns an empty list; `find_free_copy` returns `None` |
| [ ] | AV31 | All copies out of service | Reason identifies out-of-service copies and matches the service contract |
| [ ] | AV32 | All in-service copies committed | Reason contains `already committed` and matches the service contract |
| [ ] | AV33 | Blocking commitments have computable end dates | `next_free_date` follows the contract: minimum blocking effective end plus one day |
| [ ] | AV34 | Catalog availability | Contains every seeded title with consistent counts for the requested period |

## 2. Lifecycle — `tests/test_lifecycle.py`

| Done | ID | Case | Expected result |
|---|---|---|---|
| [ ] | LC01 | Asha requests Database System Concepts, 05–12 Aug; librarian approves; set business date to 05 Aug; issue; return in service | `PENDING → RESERVED → ISSUED → RETURNED`; free count decreases on submission and returns to its original value after return |
| [ ] | LC02 | Submit a valid request | Correct member, title, start, end, and allocated copy stored; status is `PENDING` |
| [ ] | LC03 | Reject a pending request with a reason | `REJECTED`; reason saved; another member can book the released dates |
| [ ] | LC04 | Reject with empty or whitespace-only reason | `REASON_REQUIRED`; request remains pending |
| [ ] | LC05 | Owner cancels a pending request | `CANCELLED`; copy commitment released |
| [ ] | LC06 | Owner cancels a confirmed reservation | `CANCELLED`; another member can book the released dates |
| [ ] | LC07 | Cancel an issued request | `INVALID_TRANSITION` |
| [ ] | LC08 | Approve a rejected request | `INVALID_TRANSITION`; rejected request remains closed |
| [ ] | LC09 | Issue a pending request | `INVALID_TRANSITION`; approval cannot be skipped |
| [ ] | LC10 | Member approves, rejects, issues, returns, or changes inventory | `NOT_AUTHORIZED`; parameterize librarian-only actions |
| [ ] | LC11 | Ravi cancels Asha's request | `NOT_AUTHORIZED` |
| [ ] | LC12 | Librarian cancels a pending request or reservation | Allowed |
| [ ] | LC13 | Librarian submits a member borrowing request | `NOT_AUTHORIZED` under the submit contract |
| [ ] | LC14 | Issue before start date | `ISSUE_NOT_ALLOWED`; message explains the start boundary |
| [ ] | LC15 | Issue after end date | `ISSUE_NOT_ALLOWED`; message explains the end boundary |
| [ ] | LC16 | Issue exactly on start date or end date | Allowed; parameterize both boundaries |
| [ ] | LC17 | Issue and return timestamps | `issued_at` and `returned_at` are recorded on their respective actions |
| [ ] | LC18 | Attempt transitions out of terminal states | `INVALID_TRANSITION`; parameterize meaningful actions on `RETURNED`, `REJECTED`, and `CANCELLED` |
| [ ] | LC19 | Authorized actor acts on nonexistent request ID | `NOT_FOUND` |
| [ ] | LC20 | Every successful lifecycle action | Exactly the expected new audit event; correct actor, from/to status, timestamp, and note |
| [ ] | LC21 | Failed lifecycle action | No request/copy mutation and no new audit event |
| [ ] | LC22 | Complete lifecycle | Original member, title, and dates remain unchanged |
| [ ] | LC23 | Approval finds allocated copy out of service and another copy free | Moves to valid replacement and approves; move logged |
| [ ] | LC24 | Approval finds allocated copy out of service and no replacement | `NO_COPY_AVAILABLE`; request remains `PENDING` |

For LC23–LC24, arrange the stale copy condition at the repository level: using the inventory service would already move or close the pending request.

## 3. Conflict, inventory, and integrity — `tests/test_edge_cases.py`

| Done | ID | Case | Expected result |
|---|---|---|---|
| [ ] | EC01 | Two distinct members fill the free Clean Code copies for 02–03 Aug; third distinct member submits | `NO_COPY_AVAILABLE`; message contains `already committed`; request count unchanged |
| [ ] | EC02 | Two distinct members request overlapping Design Patterns dates | First gets DP-1; second gets `NO_COPY_AVAILABLE`; damaged DP-2 never allocated |
| [ ] | EC03 | Same member, same title, overlapping active dates, with another copy still free | `DUPLICATE_REQUEST` |
| [ ] | EC04 | Same member and title, non-overlapping dates | Allowed if a copy is free |
| [ ] | EC05 | Duplicate check against each active status | `PENDING`, `RESERVED`, and `ISSUED` each prevent an overlapping duplicate |
| [ ] | EC06 | Prior request is rejected, cancelled, or returned | Terminal request does not prevent a new valid request |
| [ ] | EC07 | Direct `repo.insert_request` creates overlapping pending request on same copy | `sqlite3.IntegrityError`; database trigger enforces overlap protection below services |
| [ ] | EC08 | Asha reserves AIMA for 10–12 Aug, allocated AIMA-1; business date becomes 03 Aug; librarian returns Kiran's AIMA-1 loan as damaged | Asha's reservation is `MOVED`; copy ID changes to a free in-service copy; damaged AIMA-1 excluded; result and audit explain move |
| [ ] | EC09 | Asha has pending Design Patterns request on DP-1; librarian marks DP-1 under repair | Request becomes `REJECTED`; affected result reports closure; decision note contains `became unavailable` |
| [ ] | EC10 | Reserved copy becomes unavailable; no replacement free | Request becomes `CANCELLED`; reason, audit event, and affected result explain closure |
| [ ] | EC11 | Copy with current issued loan is marked out of service | Existing `ISSUED` request is not closed; pending/reserved commitments handled separately |
| [ ] | EC12 | Copy repaired and marked in service | Available again for periods without overlapping active commitments |
| [ ] | EC13 | Business date is 10 Aug; CC-1 due 04 Aug remains unreturned | CC-1 unavailable for 10–11 Aug; seeded Clean Code free count remains 2 |
| [ ] | EC14 | No single copy is free for the whole requested period, although different copies cover portions | `NO_COPY_AVAILABLE`; no partial fulfillment or substitute-title allocation |
| [ ] | EC15 | Failure during a multi-step write | Transaction rolls back request, copy, and event changes together |

Use a third distinct seeded member or create a test member for EC01. Reusing Asha or Ravi may test `DUPLICATE_REQUEST` instead of exhausted capacity.

## 4. Manual Streamlit acceptance checklist

Record actual pass/fail results and useful observations in `docs/TEST_EVIDENCE.md`.

| Done | ID | Scenario | Expected result |
|---|---|---|---|
| [ ] | UI01 | Valid and invalid login | Valid login succeeds; invalid credentials show readable error |
| [ ] | UI02 | Member and librarian page access | Role-appropriate navigation and access controls |
| [ ] | UI03 | Change catalog dates | Counts refresh and reflect whole-period availability |
| [ ] | UI04 | Happy path from PRD: Database System Concepts, 05–12 Aug | Submit, approve, advance date, issue, return; statuses and counts consistent across pages |
| [ ] | UI05 | My Requests and history | Only current member's requests; correct dates, copy, status, notes, and audit history |
| [ ] | UI06 | Exhaust Clean Code for 02–03 Aug | Third distinct member sees clear unavailability error; no new request |
| [ ] | UI07 | Request Design Patterns | Only DP-1 allocated; DP-2 shown as damaged |
| [ ] | UI08 | Reject last available commitment, then request same dates again | Reason required; released copy can be booked |
| [ ] | UI09 | Cancel last available reservation, then request same dates again | Copy can be booked; issued loans cannot be cancelled |
| [ ] | UI10 | Return damaged copy with future commitment | Replacement or closure shown explicitly, with reason and history |
| [ ] | UI11 | Past start, reversed dates, or 31-day period | Clear error; no request created; no stack trace |
| [ ] | UI12 | Business-date override | Issue boundaries and overdue availability use overridden date |
| [ ] | UI13 | Demo-data reset | Restores expected seeded users, copies, requests, and business-date behavior documented by the app |

## 5. Business-rule coverage

| Rule | Required behavior | Test mapping |
|---|---|---|
| BR1 | Request associated with member, title, start and return dates | LC02, LC22 |
| BR2 | Availability computed per physical copy for whole period | AV15–AV24, EC14 |
| BR3 | No overlapping active commitments on same copy | AV01–AV06, AV23, EC01, EC07 |
| BR4 | Prevent submission when no copy available | EC01, EC02, EC14 |
| BR5 | Operationally unavailable copies excluded | AV22, EC02, EC08–EC12 |
| BR6 | Review before reservation or loan | LC01, LC02, LC09 |
| BR7 | Rejected request closed; commitment released; revised details need new request | LC03, LC08, LC22, EC06 |
| BR8 | Reservation cancellation before issue releases copy | LC06, LC07, UI09 |
| BR9 | Return releases copy unless its condition makes it unavailable | LC01, EC08, UI10 |
| BR10 | No partial fulfillment or automatic alternative-title recommendations | EC14, UI06 |

## 6. Execution and evidence

Run from the project root:

```powershell
python -m pytest -v
```

For targeted runs:

```powershell
python -m pytest tests/test_availability.py -v
python -m pytest tests/test_lifecycle.py -v
python -m pytest tests/test_edge_cases.py -v
```

- [ ] Automated test files implemented and run.
- [ ] Failures reported to P2/P3/P4 with failing test name, expected result, and actual result.
- [ ] Core suite green on main after integration.
- [ ] Real `pytest -v` output copied into `docs/TEST_EVIDENCE.md` with revision and business-date context.
- [ ] Manual demo checklist records actual pass/fail results.
- [ ] Every BR1–BR10 rule mapped to an implemented test in evidence.
- [ ] `docs/ARCHITECTURE.md` includes layers, state machine, ER diagram, and rule ownership.
- [ ] Bonus considered only after core demo passes and the team agrees.
