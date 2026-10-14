# 01 · Problem Statement

> **Stage:** Discover · **Owner:** P1 · **Source:** [problem-statement.pdf](problem-statement.pdf)
> **Next:** [02 · Stakeholders & Workflows](02-stakeholders-and-workflows.md)

---

## 1. Context
A university library lends books to students for coursework, technical preparation, research, placements and general learning. A title can have several physical copies. Some titles have few copies and high demand.

Today, requests, reservations, issue records and returns are handled through **registers, spreadsheets and informal communication**. That worked at small scale and is breaking as usage grows.

```
                         TODAY (manual)
  +-----------+   asks in person / chat   +-------------+
  |  Student  | ------------------------> |  Librarian  |
  +-----------+                           +------+------+
        ^                                        |
        |   "maybe", "come back later"           | checks / writes
        +----------------------------------------+
                                                 v
                                   +---------------------------+
                                   | Register  +  Spreadsheet  |
                                   | (no copy-level dates,     |
                                   |  updated by hand, often   |
                                   |  late or forgotten)       |
                                   +---------------------------+
```

## 2. Pain points, and what each one demands of the system
| # | Pain point (from the PDF) | Root cause | What the system must do | Rule |
|---|---|---|---|---|
| P1 | Conflicting requests for limited copies | No single record of which copy is promised to whom and when | Commit a **specific copy** for a **date range**. Never overlap. | BR2, BR3 |
| P2 | Books requested without considering availability | Availability isn't checked at request time | Check availability **before** a request can be submitted | BR4 |
| P3 | Limited visibility into request and loan status | Status lives in a librarian's head or spreadsheet | Every request has one explicit **status**, visible to the member | BR6, BR10 |
| P4 | Delays in reviewing and confirming requests | Requests arrive through informal channels | A single **review queue** for librarians | BR6 |
| P5 | Copies stay unavailable after cancellations or returns | Manual register updates are forgotten | Release a copy **automatically** when a request is cancelled, rejected or returned | BR7, BR8, BR9 |
| P6 | Temporary unavailability from damage or repair | Copy condition isn't tracked | Track a **copy status**. Never lend a restricted copy. | BR5 |
| P7 | Different stakeholders need different information and capabilities | One shared spreadsheet for everyone | **Role-based** views and actions (member vs librarian) | see 02 |

## 3. Problem statement (one line)
> **How might we** let library members reliably reserve and borrow specific physical copies for a chosen period, and let librarians review, issue and take back those copies, **without ever double-booking a copy** and with every status and refusal visible and explained?

## 4. Goals and non-goals
**Goals**
- G1. One connected lifecycle: **request → review → reservation → loan → return**, plus reject and cancel.
- G2. Availability that is **correct per physical copy, per date range**.
- G3. **Clear refusals.** The user always knows why something was not allowed.
- G4. A prototype that **every team member can run and explain**.

**Non-goals** (see [04 · Scope](04-assumptions-and-scope.md))
- Fines, renewals, waitlists, notifications, recommendations, multi-branch, production security.

## 5. Success criteria (how we know we solved it)
| # | Criterion | How we prove it |
|---|---|---|
| S1 | No copy is ever committed to two overlapping active requests | An automated test, plus a DB trigger test that bypasses the app layer |
| S2 | A request with no free copy for the whole period is refused **before** it exists, with a reason | A test plus a live demo of the conflict scenario |
| S3 | Reject, cancel and return each make the copy available again | Tests: free count before = after |
| S4 | At least one full end-to-end flow works in the UI | Live demo: request → approve → issue → return |
| S5 | Restricted copies are never allocated | Test: the damaged *Design Patterns* copy is never chosen |
| S6 | Every member can explain one rule, one part of the code, and one trade-off | Rehearsal before the demo |

## 6. Constraints (from the PDF)
| Constraint | Effect on our solution |
|---|---|
| **90 minutes**, team of 7 | Contract-first design, parallel work, a small reliable scope |
| Locally runnable, with a UI | Streamlit + SQLite on a laptop |
| Python preferred | Python 3.10+ |
| No cloud, external APIs, paid services or complex infrastructure | Stdlib `sqlite3`. Streamlit is the only runtime dependency. |
| Authentication optional; explain it if used | Simple login; rationale in [04](04-assumptions-and-scope.md) |
| Shared GitHub repo showing incremental collaboration | One branch per person, small commits ([09](09-development-plan.md)) |

## 7. Initial library data (from the PDF, unchanged in meaning)
| Book title | Category | Total copies | Current information |
|---|---|---|---|
| Clean Code | Software Engineering | 4 | 2 copies issued until 4 Aug 2026 |
| Introduction to Algorithms | Algorithms | 3 | 1 copy reserved 4 Aug 2026 → 8 Aug 2026 |
| Design Patterns | Software Design | 2 | 1 copy unavailable due to damage |
| Database System Concepts | Databases | 5 | All copies available |
| Artificial Intelligence: A Modern Approach | Artificial Intelligence | 3 | 1 copy issued until 4 Aug 2026; 1 copy reserved 6 → 7 Aug 2026 |

How this maps to records: [04 · Assumptions §4](04-assumptions-and-scope.md#4-seed-data-interpretation).

## 8. How we are evaluated
```
  Problem understanding ........ 20%   -> docs 01-05
  Implementation & completeness  20%   -> working flows, clean code (07, 08)
  AI usage ..................... 20%   -> how we directed and validated AI (12)
  Collaboration & communication  20%   -> git history, 2-slide pitch (09, 13)
  Quiz ......................... 20%   -> already done
```
