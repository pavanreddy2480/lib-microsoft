# 02 · Stakeholders & Workflows

> **Stage:** Discover · **Owner:** P1
> **Prev:** [01 · Problem Statement](01-problem-statement.md) · **Next:** [03 · Business Rules](03-business-rules.md)

---

## 1. Stakeholder map
```
                 HIGH influence on the system
                            ^
                            |
     Library Head / Admin   |   Librarian (circulation staff)
     - sets lending policy  |   - reviews, issues, takes returns
     - wants usage insight  |   - records damage / repair
       [KEEP SATISFIED]     |     [MANAGE CLOSELY]  <-- primary user
                            |
  LOW ----------------------+----------------------> HIGH interest
                            |
     IT / Accounts / Faculty|   Member (student / researcher)
     - SSO, fines, course   |   - wants a copy for specific dates
       reserves             |   - wants to know status fast
       [MONITOR]  (out of   |     [KEEP INFORMED]  <-- primary user
        scope for 90 min)   |
                            v
                 LOW influence
```

## 2. Personas
### Asha: the Member (student)
- **Goal:** get *Introduction to Algorithms* for the week before her exam.
- **Frustration today:** walks to the library to find all copies "promised" to someone, or gets told "yes" by chat and later finds no copy.
- **Needs:** see real availability for **her dates**, request in one step, know whether she's been approved, cancel if her plans change.

### Library Staff: the Librarian
- **Goal:** process requests fairly and fast, and keep accurate records.
- **Frustration today:** cross-checks a register against a spreadsheet, forgets to free copies after returns, and has no record of damaged copies.
- **Needs:** one review queue, clear issue and return actions, the ability to mark a copy damaged or under repair, and confidence the system will not double-book.

### Library Head: the Admin (secondary)
- **Goal:** sensible policy (loan length) and visibility of usage and inventory health.
- **In the prototype:** policy is a constant (30 days), and the inventory page shows copy health. Analytics is a possible bonus.

## 3. Capability matrix (who can do what)
| Capability | Member | Librarian | System |
|---|:---:|:---:|:---:|
| Log in | Y | Y | |
| Browse catalog and availability for dates | Y | Y | |
| Submit a borrowing request | Y | | |
| View own requests and history | Y | | |
| Cancel own PENDING / RESERVED request | Y | | |
| Cancel any PENDING / RESERVED request | | Y | |
| Approve / reject a request (with reason) | | Y | |
| Issue a reserved book | | Y | |
| Return a loan and record its condition | | Y | |
| Change a copy's status | | Y | |
| Allocate a copy / release a copy | | | Y (automatic) |
| Re-allocate bookings when a copy goes out of service | | | Y (automatic) |
| Write an audit event for every change | | | Y (automatic) |

## 4. Workflows (prioritised)
| Priority | Workflow | Business rules |
|---|---|---|
| **W1 (must)** | Request → review → reservation → issue → return | BR1-BR6, BR9 |
| **W2 (must)** | Reject a request (reason required) | BR7 |
| **W3 (must)** | Cancel a pending request or confirmed reservation | BR8 |
| **W4 (must)** | Refuse an unavailable or invalid request with a reason | BR4, BR10 |
| **W5 (should)** | Return damaged, or mark a copy out of service, and handle its future bookings | BR5, BR9 |
| W6 (could) | Bonus: dashboard of overdue / due-soon loans and utilisation | - |

### W1: Happy path (swimlane)
```
 MEMBER                     SYSTEM                              LIBRARIAN
 ------                     ------                              ---------
 pick title + dates  --->   validate dates
                            find a free IN_SERVICE copy
                            create request [PENDING]
                            (copy now committed)
 sees "PENDING"      <---
                                                        <---   opens review queue
                            [PENDING] -> [RESERVED]     <---   approve
 sees "RESERVED"     <---
                                                               (start date arrives)
                            [RESERVED] -> [ISSUED]      <---   issue book
 has the book
 returns the book    -------------------------------------->   receives book
                            [ISSUED] -> [RETURNED]      <---   return (condition OK)
                            copy is free again
```

### W2 / W3: Reject and cancel
```
 [PENDING] --librarian reject (reason)--> [REJECTED]   copy released, request closed
 [PENDING] --member withdraw-----------> [CANCELLED]  copy released
 [RESERVED]--member/librarian cancel---> [CANCELLED]  copy released (only before issue)

 A REJECTED request is never edited. To try again, the member creates a NEW request.
```

### W4: Refusal before submission
```
 MEMBER ravi: "Design Patterns, 07-08 Aug"   (meera already holds DP-1 05-10 Aug)
    |
    v
 validate dates ----- fail ---> "Start date cannot be in the past" (no request created)
    | ok
    v
 any IN_SERVICE copy free for the WHOLE period?
    |                     |
   yes                    no
    |                     v
    v               "All 1 in-service copies of 'Design Patterns' are already
 create PENDING      committed for overlapping dates. A copy is next free
                     from 11 Aug 2026."  (no request created)
```

### W5: Copy goes out of service with future bookings
```
 Librarian: return loan on CC-3 as DAMAGED   (or Inventory: mark CC-3 UNDER_REPAIR)
    |
    v
 CC-3.status = DAMAGED  --> for each future PENDING/RESERVED booking on CC-3:
                               |
               another IN_SERVICE copy free for the same dates?
                    |                                   |
                   yes                                  no
                    v                                   v
          MOVE booking to that copy          CLOSE booking with reason
          (event: "moved CC-3 -> CC-4")      PENDING -> REJECTED
                                             RESERVED -> CANCELLED
                    \___________________________________/
                                   v
                 librarian sees the list of affected bookings
                 (nothing changes silently)
```
