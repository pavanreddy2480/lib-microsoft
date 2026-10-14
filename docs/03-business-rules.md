# 03 · Business Rules

> **Stage:** Define · **Owner:** P1 (rules) / P3 + P4 (enforcement)
> **Prev:** [02 · Stakeholders & Workflows](02-stakeholders-and-workflows.md) · **Next:** [04 · Assumptions & Scope](04-assumptions-and-scope.md)

There are three kinds of rule:
- **BR**: business rules from the problem statement. These are non-negotiable.
- **PR**: policy rules the team decided, to fill gaps in the PDF. They are documented in [04](04-assumptions-and-scope.md).
- **IR**: integrity rules the database enforces as a safety net.

---

## 1. Core concepts
```
  TITLE  "Clean Code"                (what members ask for)
    |
    +-- COPY  CC-1  [IN_SERVICE]     (what is actually lent)
    +-- COPY  CC-2  [IN_SERVICE]
    +-- COPY  CC-3  [DAMAGED]        <- never allocated
    +-- COPY  CC-4  [IN_SERVICE]

  REQUEST  = member + title + copy + [start .. end] + status
  COMMITMENT = a request whose status is ACTIVE (PENDING / RESERVED / ISSUED)
```

## 2. Business rules (from the PDF)
| ID | Rule | Why it exists | Enforced in | Error code |
|---|---|---|---|---|
| **BR1** | A request has one member, one title, a start date and an expected return date. | No ambiguous bookings | `lending.submit_request` + NOT NULL columns | `INVALID_DATES` |
| **BR2** | Availability is computed from individual **physical copies** for the requested period. | A title-level count can't tell *which* copy is free *when* | `availability.free_copies` | - |
| **BR3** | A copy must **never** have two overlapping active commitments. | This is the root cause of conflicts (P1) | `availability.is_copy_free` + **IR1 trigger** | `NO_COPY_AVAILABLE` |
| **BR4** | A request is refused **before submission** if no copy is free for the **whole** period. | Stops requests "without considering availability" (P2) | `lending.submit_request` | `NO_COPY_AVAILABLE` |
| **BR5** | Damaged, under-repair, lost, reference-only and restricted copies are **never** allocated. | Physical reality | `availability.is_copy_free` (`status == IN_SERVICE`) | - |
| **BR6** | Every submitted request is **reviewed** before it becomes a reservation or loan. | Library control over lending | Submit creates `PENDING` only; approve and reject are librarian-only | `NOT_AUTHORIZED` |
| **BR7** | Rejection **closes** the request and releases its copy. It is never edited or resubmitted; the member creates a new one. | Clean history; no "zombie" requests | `REJECTED` is terminal; there is no edit API | `INVALID_TRANSITION` |
| **BR8** | A confirmed reservation can be **cancelled before issue**, releasing its copy. | Plans change; free the copy for others | `lending.cancel_request` | `INVALID_TRANSITION` if ISSUED |
| **BR9** | A **return** releases the copy, unless the copy is marked unavailable during the return. | Copies must not stay blocked (P5) | `lending.return_loan(condition=...)` | - |
| **BR10** | Every refusal is **explained**. No partial fulfilment and no alternative suggestions. | Visibility (P3) | `BusinessRuleError.message` → `st.error` | all |

## 3. Policy rules (team decisions)
| ID | Rule | Enforced in | Error code |
|---|---|---|---|
| **PR1** | Dates are **inclusive**. `start >= today`, `end >= start`, and the period is **at most 30 days** (`end - start + 1 <= 30`). | `availability.validate_period` | `START_IN_PAST`, `INVALID_DATES`, `PERIOD_TOO_LONG` |
| **PR2** | A member can't hold two **overlapping active** requests for the **same title**. | `lending.submit_request` | `DUPLICATE_REQUEST` |
| **PR3** | Approval re-checks that the allocated copy is still IN_SERVICE. If it isn't, the request moves to another free copy; if none is free, approval is refused. | `lending.approve_request` | `NO_COPY_AVAILABLE` |
| **PR4** | A reservation can be issued only when `start <= today <= end`. | `lending.issue_loan` | `ISSUE_NOT_ALLOWED` |
| **PR5** | An **overdue** loan keeps its copy blocked until it is returned. Its blocking end is `max(end_date, today)`. | `availability.effective_end` | - |
| **PR6** | When a copy goes out of service, its future PENDING and RESERVED bookings are **moved** to another free copy, or **closed** with a reason. The librarian always sees the list. | `lending._handle_copy_out_of_service` | - |
| **PR7** | Rejection requires a reason. | `lending.reject_request` | `REASON_REQUIRED` |
| **PR8** | Only the **owner or a librarian** can cancel. Only a **librarian** can approve, reject, issue, return or change a copy's status. | `auth.require_role` + ownership check | `NOT_AUTHORIZED` |
| **PR9** | Requests are **immutable**: dates, title and member never change after submission. To change them, cancel and create a new request. | No update API exists | - |
| **PR10** | Every status change and reallocation writes an **audit event** (who, when, from, to, note). | `repo.insert_event` in every service | - |
| **PR11** | Allocation is **deterministic**: the first free copy by copy code. | `availability.find_free_copy` | - |
| **PR12** | "Today" is the **business date** (default 2026-08-01), never the system clock. | `clock.business_today()` | - |

## 4. Integrity rules (database safety net)
| ID | Rule | Where |
|---|---|---|
| **IR1** | Inserting or updating an ACTIVE request that overlaps another ACTIVE request **on the same copy** aborts with `COPY_OVERLAP`. | `schema.sql` triggers |
| **IR2** | `end_date >= start_date` | `CHECK` constraint |
| **IR3** | Status values are limited to the state model's values | `CHECK` constraints |
| **IR4** | Requests reference a real member, title and copy | Foreign keys (`PRAGMA foreign_keys = ON`) |
| **IR5** | Usernames, copy codes and titles are unique | `UNIQUE` constraints |

## 5. Rules in pictures

### 5.1 Overlap (inclusive dates): BR3, PR1
```
 Copy CC-3          Aug:  01  02  03  04  05  06  07  08
 existing RESERVED             [==========]                  02 -> 04
 new request A                         [==========]          04 -> 06   OVERLAP on 04 -> refused
 new request B                             [======]          05 -> 06   OK (returned 04, lent 05)

 overlap(a, b)  <=>  a.start <= b.end  AND  b.start <= a.end
```

### 5.2 Whole-period availability: BR4 (no partial fulfilment)
```
 Title with 2 copies, request 03 -> 06
                    Aug:  01  02  03  04  05  06  07
 copy X  booked                [======]                    02 -> 04   blocks 03-04
 copy Y  booked                            [======]        05 -> 07   blocks 05-06
 request                           [==============]        03 -> 06

 X is free only on 05-06, and Y only on 03-04. NO single copy is free for the WHOLE period.
 -> refused. We never split one request across two copies.
```

### 5.3 Overdue loan: PR5
```
 business date = 10 Aug
 CC-1 ISSUED 21 Jul -> 04 Aug, not returned yet
                    Aug:  04  05  06  07  08  09  10  11  12
 planned loan        ==]
 effective block     ===========================]            until max(04, 10) = 10
 request 10 -> 11                               [======]     OVERLAP -> CC-1 not offered
 request 12 -> 13                                       [==  allowed (see critique in 05)
```

### 5.4 Which statuses hold a copy
```
              holds copy?
 PENDING        YES   (committed at submission)
 RESERVED       YES
 ISSUED         YES   (until actually returned)
 ---------------------------------------------
 REJECTED       no    -> released
 CANCELLED      no    -> released
 RETURNED       no    -> released (copy status may become DAMAGED/LOST at return)

 "Releasing" a copy is not a separate action: it happens automatically when the
 request leaves an ACTIVE status.
```

## 6. Allowed status transitions (the only legal moves)
| From \ To | RESERVED | ISSUED | RETURNED | REJECTED | CANCELLED |
|---|:---:|:---:|:---:|:---:|:---:|
| **PENDING** | approve | - | - | reject | cancel |
| **RESERVED** | - | issue | - | - | cancel |
| **ISSUED** | - | - | return | - | - |
| **REJECTED / CANCELLED / RETURNED** | - | - | - | - | - |

Source of truth: `ALLOWED_TRANSITIONS` in `src/lms/domain/models.py`. Any other move raises `INVALID_TRANSITION`.
