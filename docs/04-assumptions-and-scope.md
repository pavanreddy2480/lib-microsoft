# 04 · Assumptions & Scope

> **Stage:** Define · **Owner:** P1
> **Prev:** [03 · Business Rules](03-business-rules.md) · **Next:** [05 · Critique & Open Questions](05-critique-and-open-questions.md)

The PDF allows extra assumptions "provided they are documented and applied consistently". These are ours. Each one is applied in exactly one place in the code, shown in *Enforced in*. That column was contributed by P1.

---

## 1. Assumptions
| ID | Assumption | Why | Enforced in | If it turns out wrong |
|---|---|---|---|---|
| **A1** | A **specific copy is committed at submission**, so a PENDING request already holds it. | BR3 lists "active borrowing requests" as commitments, and BR7 says rejection *releases* a copy. Both imply a pending request holds one. | `lending.submit_request` → `availability.find_free_copy` | Move allocation to approval. This only changes `submit_request` and `approve_request`. |
| **A2** | Dates are **inclusive**. A copy due on 4 Aug can be lent from 5 Aug. | Simple, safe and easy to explain | `availability.overlaps` + `schema.sql` triggers `trg_no_overlap_insert/update` | Change one comparison in `overlaps()` and the trigger |
| **A3** | "Today" is a **business date**, default **2026-08-01**, adjustable in the sidebar. | The PDF data is dated Aug 2026 and the real date is later, which would make all seed loans overdue. The demo also needs to "move time" to issue and return. | `domain/clock.py` + sidebar in `ui/common.py` | Set the default to `date.today()` |
| **A4** | The maximum borrowing period is **30 days**. The start can't be in the past. | Team decision; the PDF gives no policy | `availability.validate_period`, `models.MAX_PERIOD_DAYS` | `MAX_PERIOD_DAYS` constant |
| **A5** | One member can't hold overlapping active requests for the same title. | Prevents hoarding scarce copies | `lending.submit_request` | Remove the check in `submit_request` |
| **A6** | Approval creates a **confirmed reservation**. **Issue** is a separate step, allowed only within `[start, end]`. | Matches the PDF's "confirmed reservation **or** loan" and mirrors the physical hand-over | `models.ALLOWED_TRANSITIONS`, `lending.issue_loan` | - |
| **A7** | An **overdue** loan blocks its copy until it is actually returned. | The book isn't on the shelf | `availability.effective_end` (ISSUED end = max(end, today)) | - |
| **A8** | When a copy goes out of service, its future bookings are **auto-moved** to another free copy, or **closed** with a reason. | "Existing commitments must not be silently overwritten." This is the least disruptive option for members. | `lending._handle_copy_out_of_service` (via `set_copy_status` / `return_loan`); PENDING/RESERVED only, ISSUED untouched | Switch the policy to "block the status change" |
| **A9** | Members may **withdraw** their own PENDING request (recorded as CANCELLED). | Natural need; it reuses the cancel path | `lending.cancel_request` | - |
| **A10** | Seed data: issue **start dates** are missing from the PDF, so they are reconstructed as **due date − 14 days**. "1 issued + 1 reserved" means **two different copies**. | Keeps the PDF's meaning without inventing conflicts | `persistence/seed.py` | Edit `seed.py` |
| **A11** | **Simple login**: username and password, sha256 with a static salt, roles MEMBER and LIBRARIAN. | Makes "who is acting" real, which matters for ownership checks and librarian-only actions. A role dropdown would let anyone approve. | `services/auth.py`, `domain/security.py` | Replace with SSO in production |
| **A12** | A request is always for **one copy of one title**. | The PDF defines the request this way | `lending.submit_request` (one `copy_id` per request) | - |
| **A13** | The business date is **shared by all users** of one running app. | A demo convenience | `domain/clock.py` (module-level date) | Per-session date, or the real clock |

## 2. Scope (MoSCoW)
| Priority | Item | Workflow / rule |
|---|---|---|
| **Must** | Login + role-gated pages | A11 |
| **Must** | Catalog with copy-level availability for chosen dates | BR2 |
| **Must** | Submit a request with validation and a clear refusal reason | BR1, BR4, BR10, PR1, PR2 |
| **Must** | Review queue: approve / reject with reason | BR6, BR7 |
| **Must** | Cancel a pending or reserved request | BR8 |
| **Must** | Issue and return, recording the copy condition | BR9, PR4 |
| **Must** | DB-level overlap protection + a transaction per action | BR3, IR1 |
| **Must** | Seed data from the PDF + a demo reset | - |
| **Must** | Automated tests for every BR | - |
| **Should** | Inventory: change copy status with reallocation | BR5, PR6 |
| **Should** | Audit trail per request, visible in the UI | PR10 |
| **Should** | Overdue badge | PR5 |
| **Could** | Bonus: dashboard (overdue, due soon, utilisation) | - |
| **Won't** | see §3 | - |

## 3. Out of scope (and why)
| Excluded | Reason |
|---|---|
| Partial fulfilment, alternative-book suggestions | Explicitly not required (BR10) |
| Fines and penalties | Not in the problem. It needs payment policy. |
| Renewals / loan extensions | Would need date edits, which conflicts with immutable requests (PR9). Future work. |
| Waitlists / holds queue | Adds a second allocation path. Too big for 90 minutes. |
| Email / SMS notifications | No external services allowed |
| Multiple branches, barcode/RFID, SSO | Infrastructure we don't have |
| Production-grade security (per-user salt, lockout, HTTPS) | A prototype. Documented as a limitation. |
| Pagination, search at scale | The data is tiny |

## 4. Seed data interpretation
| PDF says | Our records |
|---|---|
| Clean Code, 4 copies, "2 copies issued until 4 Aug 2026" | CC-1 (asha) and CC-2 (ravi) **ISSUED** 21 Jul → 4 Aug. CC-3 and CC-4 free. |
| Introduction to Algorithms, 3 copies, "1 copy reserved 4 → 8 Aug" | ITA-1 (meera) **RESERVED** 4 → 8 Aug. ITA-2 and ITA-3 free. |
| Design Patterns, 2 copies, "1 copy unavailable due to damage" | DP-2 status **DAMAGED**. DP-1 free. |
| Database System Concepts, 5 copies, "all available" | DSC-1 … DSC-5 free |
| AI: A Modern Approach, 3 copies, "1 issued until 4 Aug and 1 reserved 6 → 7 Aug" | AIMA-1 (kiran) **ISSUED** 21 Jul → 4 Aug. AIMA-2 (asha) **RESERVED** 6 → 7 Aug. AIMA-3 free. |

```
 Seed commitments (business date 01 Aug = "today")
                          Jul 21 ...   Aug 01  02  03  04  05  06  07  08
 CC-1   asha   ISSUED     [=========================]
 CC-2   ravi   ISSUED     [=========================]
 ITA-1  meera  RESERVED                              [================]
 AIMA-1 kiran  ISSUED     [=========================]
 AIMA-2 asha   RESERVED                                      [======]
 DP-2          DAMAGED    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (never lendable)
                                        ^ today
```

Demo accounts: `librarian / lib123`. Members `asha`, `ravi`, `meera`, `kiran` / `pass123`.
