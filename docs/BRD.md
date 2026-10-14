# Business Requirements Document: Library Management System

*Draft v0.1 (interface phase). Owner: Person 1, who refines it during the build.*

## 1. Problem
A university library coordinates book requests, reservations, issues and returns using registers, spreadsheets and informal messages. This causes:
- conflicting requests for scarce copies (the same copy is promised twice)
- books requested without checking availability
- little visibility into request and loan status for students or staff
- slow review and confirmation
- copies stuck as "unavailable" after a cancellation or return
- no tracking of damaged or under-repair copies
- different stakeholders needing different information and actions

**Business goal:** one reliable system of record that never double-books a physical copy, makes every request's status visible, and ensures each copy is freed exactly when it should be.

## 2. Stakeholders and personas
| Persona | Needs | In the prototype |
|---|---|---|
| **Member** (student or researcher) | See what is available for my dates, request it, track status, cancel if plans change | Yes: Member role |
| **Librarian** (circulation staff) | Review requests, confirm, issue, take returns, record damage | Yes: Librarian role |
| **Library head / admin** | Policy (loan length), usage visibility, inventory health | Partly: inventory page, plus a possible analytics bonus |
| Faculty, accounts/fines, IT | Course reserves, fines, SSO integration | Out of scope |

## 3. Core workflows (prioritised)
1. **Request → review → reservation → issue → return.** This is the main end-to-end flow.
2. **Rejection** by the librarian, with a reason. The request is closed and the copy released.
3. **Cancellation** of a pending request or confirmed reservation before issue. The copy is released.
4. **Return with condition.** If the copy comes back damaged or lost, it is taken out of service and its future commitments are handled.
5. **Inventory status change.** Mark a copy damaged, under repair, lost, reference-only, restricted, or back in service.

## 4. Business rules (from the problem statement, BC1 to BC10)
| ID | Rule |
|---|---|
| BR1 | A request has exactly one member, one title, a start date and an expected return date. |
| BR2 | Availability is computed per physical copy for the requested period. |
| BR3 | A copy never has two overlapping active commitments (pending request, reservation or loan). |
| BR4 | A request cannot be submitted if no copy is free for the **whole** period. No partial fulfilment and no alternative suggestions. |
| BR5 | Damaged, under-repair, lost, reference-only and restricted copies are never allocated. |
| BR6 | Every submitted request is reviewed before it becomes a reservation or loan. |
| BR7 | Rejection closes the request and releases the copy. A rejected request is never edited or resubmitted; the member creates a new one. |
| BR8 | A confirmed reservation can be cancelled before issue, releasing the copy. |
| BR9 | A return releases the copy unless it is marked unavailable during the return. |
| BR10 | Every refusal tells the user why. |

## 5. Assumptions (team decisions; also in ASSUMPTIONS.md)
- A1. A **specific copy is committed at submission**. A pending request already holds it, which is why BC7 says rejection must "release" a copy.
- A2. Dates are **inclusive**. A copy due back on 4 Aug can be lent from 5 Aug.
- A3. **Business date** defaults to 2026-08-01 so the PDF data is meaningful. It can be changed in the sidebar for demos.
- A4. The maximum borrowing period is **30 days**. The start date cannot be in the past.
- A5. A member cannot hold two overlapping active requests for the same title.
- A6. Approval produces a **confirmed reservation**. Issue is a separate librarian action allowed only within [start, end].
- A7. An overdue loan keeps blocking its copy until it is actually returned.
- A8. If a copy goes out of service while it has future commitments, each one is **moved to another free copy**. If none is free, it is closed with a recorded reason. Nothing changes silently.
- A9. Members may withdraw their own pending request (treated as a cancellation).
- A10. Seed data: issue start dates are not given, so they are reconstructed as 14 days before the due date. "1 issued + 1 reserved" means two different copies.
- A11. Simple username/password login (demo-grade hashing). Login was prioritised so that member identity and the librarian-only actions are real rather than simulated.

## 6. Scope
**In:** the workflows in §3, both roles, login, copy-level availability, an audit trail per request, seeded PDF data, a demo reset, and automated tests.
**Out:** fines, renewals, waitlists and holds queues, notifications by email or SMS, alternative-book suggestions (excluded by BC10), partial fulfilment, multiple branches, barcode or RFID, SSO, cloud deployment, and production-grade security.

## 7. Open questions (to raise with the client)
- What is the real loan-length policy per member type (UG, PG, faculty)?
- Should there be a limit on concurrent loans per member?
- What happens to a member whose reserved copy is lost and no replacement exists? (We close the request with a reason and assume notification is manual.)
- Should overdue loans block a member from new requests?
