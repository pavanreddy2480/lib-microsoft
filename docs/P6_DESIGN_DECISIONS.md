# Librarian UI: design decisions (Person 6)

Scope: `app/pages/3_Review_Queue.py`, `4_Loans.py`, `5_Inventory.py` and the support package `src/lms/ui/librarian/`.
Rules these screens make visible: BR5 (restricted copies are never allocated), BR6 (every request is reviewed), BR7 (reject releases), BR8 (cancel before issue), BR9 (return releases unless marked unavailable), BR10 (refusals say why).

## 1. The problem I had to design around

The services and persistence layers were still `NotImplementedError` when I started, so the pages could not be run or tested against real code. The pages also had to stay thin (CONTEXT.md §5: "pages never decide whether something is allowed"). Both pushed towards the same design: pages talk to an interface, and the real services sit behind an adapter.

## 2. Structure

```
app/pages/3_,4_,5_*.py          declarative pages: layout + wiring only
        │
lms.ui.librarian.components     flash(), act()  (Streamlit glue)
lms.ui.librarian.presenters     pure functions: ordering, overdue, filtering, wording
        │
lms.ui.librarian.registry       get_port() / set_port()  (override seam)
        │
lms.ui.librarian.port           LibrarianPort (Protocol)
   ├── service_port.ServicePort  → lending / repo / db / seed / clock   (production)
   └── tests/p6/fakes.InMemoryPort                                      (tests)
```

Dependencies still point downward only. `presenters` and `views` import no Streamlit and no database code.

## 3. Patterns used, and why each one earned its place

| Pattern | Where | Why this and not something simpler |
|---|---|---|
| **Ports & Adapters / Dependency Inversion** | `LibrarianPort` + `ServicePort` | The pages can run and be tested before P2–P4 merge, and the real wiring is one swap. Without it, every page test would need a seeded database. |
| **Adapter** | `ServicePort` | Translates ids and repository dataclasses into UI-ready rows (member names, copy codes). The only librarian-UI code that touches `lending`, `repo`, `db`, `seed`, `clock`. |
| **Facade** | `LibrarianPort` as seen by pages | One small surface (approve, reject, issue, return, …) instead of five modules. Pages never open connections. |
| **Presenter / View-model** | `presenters.py`, `views.py` | Display decisions (oldest first, overdue badge, filter, message wording) are pure functions, so unit tests need no Streamlit. Frozen DTOs stop the UI mutating domain objects. |
| **Strategy (lookup table)** | `OUTCOME_SEVERITY` | MOVED → info, CLOSED → warning. A new outcome is one dictionary entry, with a safe `warning` default. |
| **Service Locator with a test seam** | `registry.py` | Streamlit page scripts have no constructor to inject into. A tiny locator with `set_port` gives injection where the framework offers none. Chosen over a global `if TESTING` flag. |
| **Template method (helper)** | `components.act()` | Every button does the same thing: call through `run_action`, flash a message, `st.rerun()`. One helper removes eleven copies of that sequence and guarantees errors never skip `run_action`. |
| **Observer-like message queue** | `flash()` / `show_flash()` | `st.rerun()` wipes anything drawn before it. Queueing messages in `session_state` and draining them once at the top of the next run keeps the confirmation and the MOVED/CLOSED warnings visible. |

Patterns I deliberately did not use: a state machine in the UI (the state model lives in `domain.models` and `lending`; duplicating it would create a second source of truth), and an event bus (nothing else in the UI reacts to these actions).

## 4. Decisions and trade-offs

1. **Business rules stay out of the UI.** The page never checks "is this transition legal" or "is the reason blank"; it shows the service's error. Trade-off: the fake in the tests has to mimic a few rules. I limited it to what the UI can observe and run the same assertions against the fake and the real adapter (§5), so drift is detected.
2. **New files in `src/lms/ui/librarian/`, no edits to existing `src/lms/*`.** docs/team/6.md forbids editing `src/lms/*` and `ui/common.py`. Adding a new package avoids merge conflicts; `run_action` and `page_setup` are reused unchanged. I flag this because it is a small stretch of "pages only": P1 should confirm they are happy with the extra package.
3. **Copy allocated-state is shown from the repository, not recomputed.** The inventory "Next commitment" column reads `active_commitments_for_copy`. Availability maths stays in `availability.py` (single owner).
4. **Two inputs per queue row (approval note, rejection reason).** One shared box would make "required for reject, optional for approve" ambiguous.
5. **Messages survive reruns.** The spec says `st.rerun()` after a successful action. Plain `st.success` before a rerun is invisible, so confirmations go through `flash`.
6. **Reset demo data is double-guarded.** A checkbox must be ticked before the button is enabled (no `confirm()` dialogs, per the spec). The adapter also resets the business date.
7. **Compatibility.** `use_container_width` was dropped from the `st.dataframe` calls: it is deprecated in current Streamlit, and the default already fills the width there.

## 5. Test strategy

| Level | File | What it proves | Needs real services? |
|---|---|---|---|
| Unit | `test_presenters.py`, `test_registry.py`, `test_fake_policy.py` | Pure display logic, the override seam, the fake's move-or-close policy | No |
| Integration (contract) | `test_port_contract.py` | The same 13 assertions on both the fake and `ServicePort` over real SQLite: approve, reject-needs-reason, terminal reject, member not authorized, issue window, cancel, return releases / damaged, inventory, history | Real variant **skips** until P2/P3/P4 merge, then runs unchanged |
| End-to-end | `test_pages_e2e.py` | The actual page scripts run headless with Streamlit `AppTest`: guards, queue order, approve, empty-reason error, reject, issue error and success, overdue badge, damaged-return MOVED report, filters and history, inventory change and close, reset guard | No (uses the fake) |

Honest limit: until the real services land, the "real" half of the contract tests is skipped, so what is verified today is the UI against the contract, not against P4's implementation. Run `python -m pytest tests/p6 -rs` after merging P2–P4; any skip left means that dependency is still missing, and any failure is either an adapter bug or a fake that drifted.

## 6. How this maps to "be ready to explain"

- **BR6:** the Review Queue is the only place a PENDING request leaves PENDING. `test_approve_flow…`, `test_reject_…`.
- **BR9:** `ReturnOutcome` carries the request and the affected reservations; `test_return_in_service_…` vs `test_return_damaged_…`.
- **BR5:** the inventory page changes `CopyStatus`; the closing and moving of commitments is reported, never silent (`test_marking_the_only_lendable_copy_…`).
