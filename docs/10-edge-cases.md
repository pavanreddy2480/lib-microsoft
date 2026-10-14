# 10 · Edge Cases

> **Stage:** Review · **Owner:** P7 (tests), P4 (behaviour)
> **Prev:** [09 · Development Plan](09-development-plan.md) · **Next:** [11 · Test Evidence](11-test-evidence.md)

The edge-case review: every awkward situation we could think of, the **expected** behaviour, and the test that will prove it. Test names are **planned**. P7 implements them, and results go into [11 · Test Evidence](11-test-evidence.md) only after they have been run.

Legend: **Layer** = where the behaviour is enforced (S = service, A = availability, D = database, U = UI).

---

## 1. Dates (PR1)
| # | Scenario (business date 01 Aug) | Expected | Code | Layer | Planned test |
|---|---|---|---|---|---|
| E1 | Start or end date missing | refused | `INVALID_DATES` | A | `test_validate_missing_dates` |
| E2 | End before start (09 → 01 Aug) | refused | `INVALID_DATES` | A + D (CHECK) | `test_validate_end_before_start` |
| E3 | One-day loan (start = end) | **allowed** | - | A | `test_one_day_period_ok` |
| E4 | Start in the past (31 Jul) | refused | `START_IN_PAST` | A | `test_validate_start_in_past` |
| E5 | Start = today | **allowed** | - | A | `test_start_today_ok` |
| E6 | Exactly 30 days inclusive (01 → 30 Aug) | **allowed** | - | A | `test_30_days_ok` |
| E7 | 31 days (01 → 31 Aug) | refused | `PERIOD_TOO_LONG` | A | `test_31_days_refused` |

## 2. Availability (BR2-BR5, PR5)
| # | Scenario | Expected | Code | Layer | Planned test |
|---|---|---|---|---|---|
| E8 | New booking starts the day after an existing one ends | **allowed** | - | A + D | `test_adjacent_dates_ok` |
| E9 | New booking shares one day with an existing one | refused | `NO_COPY_AVAILABLE` | A + D | `test_touching_dates_overlap` |
| E10 | All copies of a title are out of service | refused, reason says "out of service" | `NO_COPY_AVAILABLE` | A | `test_all_copies_restricted_reason` |
| E11 | All in-service copies booked: *Intro to Algorithms* 05-07 Aug. ITA-1 is reserved; asha takes ITA-2 and ravi ITA-3, then kiran asks. | kiran refused; reason says "already committed" + "next free from 08 Aug" | `NO_COPY_AVAILABLE` | A | `test_all_copies_committed_refused` |
| E12 | Free days exist, but no single copy covers the whole period | refused (no split) | `NO_COPY_AVAILABLE` | A | `test_no_partial_fulfilment` |
| E13 | Overdue loan (CC-1 due 04 Aug, today 10 Aug) | CC-1 not offered for 10-11 Aug | - | A | `test_overdue_blocks_copy` |
| E14 | REJECTED / CANCELLED / RETURNED bookings on a copy | **don't** block it | - | A + D | `test_terminal_requests_do_not_block` |
| E15 | Design Patterns: DP-2 is DAMAGED | only DP-1 is ever allocated; a 2nd overlapping request is refused | `NO_COPY_AVAILABLE` | A | `test_damaged_copy_never_allocated` |
| E16 | Same member, same title, overlapping dates (e.g. asha asks for *Clean Code* 02-03 Aug while holding CC-1) | refused. The duplicate check runs **before** the availability check. | `DUPLICATE_REQUEST` | S | `test_duplicate_request` |
| E16b | Same member, same title, **non**-overlapping dates; or a different member | **allowed** | - | S | `test_non_duplicate_ok` |

```
 E12 - no partial fulfilment              E13 - overdue loan (today = 10 Aug)
 Aug:     02  03  04  05  06  07          Aug:  04  05 ... 09  10  11  12
 copy X   [======]                        CC-1 ==]  (planned end 04)
 copy Y               [======]            block  ===================]  (until today)
 request      [==============]  REFUSED   req 10-11              [======]  REFUSED
```

## 3. Lifecycle / state machine (BR6-BR9)
| # | Scenario | Expected | Code | Layer | Planned test |
|---|---|---|---|---|---|
| E17 | Approve a REJECTED request | refused | `INVALID_TRANSITION` | S | `test_approve_rejected_refused` |
| E18 | Approve twice (double-click) | 2nd refused, shown as an error, no crash | `INVALID_TRANSITION` | S + U | `test_double_approve` |
| E19 | Cancel an ISSUED loan | refused (must be returned) | `INVALID_TRANSITION` | S | `test_cancel_issued_refused` |
| E20 | Reject with an empty or whitespace reason | refused | `REASON_REQUIRED` | S | `test_reject_requires_reason` |
| E21 | Issue before the start date / after the end date | refused, says which | `ISSUE_NOT_ALLOWED` | S | `test_issue_window` |
| E22 | Return twice | 2nd refused | `INVALID_TRANSITION` | S | `test_double_return` |
| E23 | "Resubmit" a rejected request | impossible: there is no API. A **new** request for the same dates succeeds. | - | S | `test_rejected_then_new_request_ok` |
| E24 | Approve after the allocated copy was marked DAMAGED | moved to another free copy; if none, refused and the request stays PENDING | `NO_COPY_AVAILABLE` | S | `test_approve_reallocates` |
| E25 | Unknown request or copy id | refused | `NOT_FOUND` | S | `test_not_found` |
| E26 | Every action writes exactly one audit event (plus one per reallocation) | history length grows | - | S | `test_events_written` |

## 4. Authorisation (PR8, A11)
| # | Scenario | Expected | Code | Layer | Planned test |
|---|---|---|---|---|---|
| E27 | A member calls approve / reject / issue / return / set_copy_status | refused | `NOT_AUTHORIZED` | S | `test_member_cannot_approve` |
| E28 | ravi cancels asha's request | refused | `NOT_AUTHORIZED` | S | `test_cancel_other_member_refused` |
| E29 | The librarian submits a borrowing request | refused (submit is member-only) | `NOT_AUTHORIZED` | S | `test_librarian_cannot_submit` |
| E30 | Wrong password vs unknown user | **same** message for both | `LOGIN_FAILED` | S | `test_login_failed_same_message` |
| E31 | A page opened without logging in | warning, page stops | - | U | manual |
| E32 | A member opens a librarian page | error, page stops | - | U | manual |

## 5. Copy status changes (BR5, BR9, PR6)
| # | Scenario | Expected | Layer | Planned test |
|---|---|---|---|---|
| E33 | Return as DAMAGED; the copy has a future reservation; another copy is free | reservation **MOVED** (copy_id changes, event logged) | S | `test_damaged_return_moves_booking` |
| E34 | The same, but no other copy is free | **CLOSED**: RESERVED → CANCELLED, PENDING → REJECTED, with note "became unavailable" | S | `test_damaged_no_copy_closes_booking` |
| E35 | Mark a copy out of service while it's ISSUED | allowed; the loan is untouched; future bookings are handled as E33/E34 | S | `test_restrict_issued_copy` |
| E36 | Mark a copy back to IN_SERVICE | lendable again; no bookings change | S | `test_copy_back_in_service` |
| E37 | The affected list is always returned to the UI | the UI shows MOVED as info and CLOSED as a warning | S + U | part of E33/E34 + manual |

```
 E33 / E34 - copy CC-3 returned DAMAGED on 03 Aug, with req#9 RESERVED 10-12 Aug on CC-3
                     CC-4 free 10-12?
                     /            \
                   yes             no
                    |               |
   req#9.copy -> CC-4          req#9 -> CANCELLED
   event "moved CC-3->CC-4"    note "Copy CC-3 became unavailable and no other copy is free"
   AffectedRequest(MOVED)      AffectedRequest(CLOSED)
```

## 6. Integrity and concurrency (BR3, IR1)
| # | Scenario | Expected | Layer | Planned test |
|---|---|---|---|---|
| E38 | Two members submit for the last copy at the same moment | `BEGIN IMMEDIATE` serialises them: the first gets the copy, the second gets `NO_COPY_AVAILABLE` | S + D | `test_sequential_submits_last_copy` |
| E39 | Code inserts an overlapping active row directly (bypassing services) | DB aborts with `COPY_OVERLAP` | D | `test_trigger_blocks_overlap` |
| E40 | Re-activating a cancelled row that would overlap | DB aborts | D | `test_trigger_blocks_reactivation` |
| E41 | An error halfway through an action | full rollback: no status change, no event | S + D | `test_rollback_on_error` |
| E42 | Reset demo data | DB back to the PDF seed; business date back to 01 Aug | S | `test_reset_db` |

```
 E38 - why BEGIN IMMEDIATE matters
   without it:  A checks (free) -> B checks (free) -> A inserts -> B inserts  => DOUBLE BOOKING
                                                                    (trigger would still stop B)
   with it:     A: BEGIN IMMEDIATE (lock) -> check -> insert -> COMMIT
                B: BEGIN IMMEDIATE (waits) ...................-> check (not free) -> refused
```
**Already verified (contract phase):** E39, E40, adjacent dates (E8) and the end-before-start CHECK (E2, DB part) were run against `schema.sql` in an in-memory DB. See [12 · Iteration Log](12-iteration-log.md).

## 7. Open edge cases (decision needed: P4 decides, P1 records)
| # | Scenario | Gap | Recommended handling |
|---|---|---|---|
| O1 | Approving a PENDING request whose **end date has already passed** (the business date moved forward) | It would become a RESERVED booking that can never be issued | Refuse the approval with a clear message, and let the librarian reject it |
| O2 | A PENDING request whose **start date passes** without review | It keeps holding a copy (W1 in [05](05-critique-and-open-questions.md)) | Accept for the prototype. Production: auto-expire. |
| O3 | A RESERVED booking whose end date passes without being issued | It keeps holding the copy for past dates (harmless; doesn't block future dates) | Accept. The librarian can cancel it. |
| O4 | `set_copy_status` to the copy's **current** status | Not specified | No-op that returns an empty affected list |
| O5 | The business date is moved **backwards** in the demo | Existing bookings may look "in the future" or allow odd issues | Demo discipline: only move forward, and reset before presenting |

## 8. Traceability: rule → edge cases
```
 BR1  -> E1, E2              BR6  -> E17, E27         PR1  -> E1-E7
 BR2  -> E10-E15             BR7  -> E17, E23         PR2  -> E16, E16b
 BR3  -> E8, E9, E38-E40     BR8  -> E19, E28         PR4  -> E21
 BR4  -> E11, E12            BR9  -> E22, E33-E35     PR5  -> E13
 BR5  -> E10, E15, E35       BR10 -> E10, E11, E30    PR6  -> E24, E33-E37
```
