# 05 · Critique & Open Questions

> **Stage:** Challenge (the "critic" pass) · **Owner:** P1, with input from everyone
> **Prev:** [04 · Assumptions & Scope](04-assumptions-and-scope.md) · **Next:** [06 · PRD](06-prd.md)

Before building, we interrogate the requirements and our own design: what is ambiguous, what could go wrong, and where our choices are weak. A forward-deployed engineer's job is to ask these questions **before** the client finds the answers in production.

---

## 1. Ambiguities in the problem statement, and how we resolved them
| # | Question the PDF leaves open | Options | Our decision | Ref |
|---|---|---|---|---|
| Q1 | Does a **pending** request already hold a copy, or only an approved one? | at submission / at approval | **At submission.** BR3 and BR7 imply it. | A1 |
| Q2 | What is "today"? The data is Aug 2026 and the machine date is later. | real clock / shift data / configurable | **Configurable business date**, default 2026-08-01 | A3 |
| Q3 | Does approval create a **reservation** or a **loan**? | either | **Reservation**. Issue is a separate hand-over step. | A6 |
| Q4 | Is the return date inclusive? Can a copy go out the day it comes back? | inclusive / exclusive | **Inclusive.** Next lend is the following day. | A2 |
| Q5 | "1 copy issued … and 1 copy reserved": the same copy or two copies? | same / different | **Different copies** | A10 |
| Q6 | Who is the "appropriate end user" who may cancel? | member / librarian / both | **Owner or librarian** | PR8 |
| Q7 | What happens to future bookings when a copy becomes damaged or lost? | block / flag / move-or-close | **Move to another copy, else close with a reason** | A8 |
| Q8 | What is the loan-length policy? | 14 / 30 / none | **30 days max** | A4 |
| Q9 | Is authentication needed? | none / role switch / login | **Simple login** | A11 |
| Q10 | Can an overdue book be lent to the next member? | - | **No.** It blocks until returned. | A7 |

## 2. Delivery risks (90 minutes, 7 people)
| Risk | Likelihood | Impact | Mitigation |
|---|:---:|:---:|---|
| Merge conflicts from 7 people editing the same files | High | High | **One owner per file.** Contract files are frozen ([08](08-code-structure.md)). |
| Integration happens too late; nothing works at T+80 | Med | High | Contract-first stubs. P2/P3 merge by **T+35**. Fixed merge order ([09](09-development-plan.md)). |
| AI-generated code that nobody can explain | Med | High | Small modules, docstrings as the spec. Every member must explain their file. |
| Streamlit rerun pitfalls (duplicate button keys, stale state) | High | Med | Unique `key=` per button, `st.rerun()` after actions, shared `run_action` helper |
| A teammate's environment can't import `lms` | Med | Med | One setup command (`pip install -r requirements.txt`), stated at the top of every task file |
| Over-scoping (bonus before the core works) | Med | High | MoSCoW in [04](04-assumptions-and-scope.md). The bonus comes only after the core demo passes. |

## 3. Technical risks
| Risk | Mitigation |
|---|---|
| Double booking from a bug in application code | **Two layers:** the app check and the DB trigger (IR1) |
| Double booking from two simultaneous submits | `BEGIN IMMEDIATE` takes the write lock before check-then-insert |
| A half-applied action (status changed, but no event written) | One transaction per service call; rollback on any error |
| Silent change to someone's booking | PR6 always returns and logs affected bookings; PR10 audit trail |
| Paths break when run from another folder | All paths come from `lms/config.py` (tested from a foreign folder) |

## 4. Self-critique: weaknesses we knowingly accept
| # | Weakness | Example | Why we accept it | Production fix |
|---|---|---|---|---|
| W1 | **Pending requests hold copies.** Unreviewed requests can block others. | Members spam requests | PR2 limits duplicates. Review is fast at this scale. | Auto-expire PENDING after N hours |
| W2 | **First-fit allocation** can refuse a request that a reshuffle would fit. | see §4.1 | Deterministic and explainable. A reshuffle would silently move people's copies. | Best-fit allocation, or allocate at issue time |
| W3 | An **overdue** loan only blocks up to *today*. A booking starting tomorrow is allowed. | CC-1 due 04, today 10 → a request for 12-13 is accepted | We can't know when it comes back. PR6 handles a copy that is declared LOST. | Overdue grace buffer; block all future bookings on overdue copies |
| W4 | The business date is **global** to the running app | Two demo browsers see the same "today" | Demo convenience | The real clock, or a per-session date |
| W5 | **Demo-grade password hashing** | Static salt | Prototype | bcrypt/argon2, SSO |
| W6 | The DB trigger doesn't know about the overdue extension (PR5) | - | The app layer covers it; the trigger guards the planned dates | Postgres `EXCLUDE USING gist` with a computed range |
| W7 | No notifications: a member learns about a closed booking only by checking | PR6 closes a reservation | No external services allowed | Email or in-app notifications (bonus idea) |

### 4.1 Why first-fit can be suboptimal (W2)
```
 2 copies. Existing bookings:  A: 01-03    B: 07-09
                     Aug:  01  02  03  04  05  06  07  08  09
 copy A                    [==========]
 copy B                                            [==========]

 1) X requests 05-06 -> first free copy is A          A: 01-03, 05-06
 2) Y requests 04-08 -> A clashes with X (05-06), B clashes with 07-09 -> REFUSED

 If X had been put on B (B is free on 05-06), then A would be free for 04-08.
 We accept this: allocation is predictable, and we never move a booking behind a member's back.
```

## 5. Questions we would put to the client (post-hackathon)
1. What is the real **loan length** per member type (UG / PG / faculty)? Are renewals allowed?
2. Is there a limit on **concurrent loans** per member?
3. Should overdue members be **blocked** from new requests? Are there fines?
4. How quickly must a librarian **review** a request? Should unreviewed requests expire?
5. When a reserved copy is lost and no replacement exists, how should the member be **notified**?
6. Do reference-only copies need an **in-library use** workflow?
7. Is there a **holds queue** expectation (first come, first served) for popular titles?
8. Should **librarians be able to book on behalf of** a member (walk-in)?
9. Who can see **who borrowed what**? Are there privacy requirements?
10. Which systems must this integrate with later (student SSO, ERP, barcode scanners)?
