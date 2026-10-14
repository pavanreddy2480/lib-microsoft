# 11 · Test Evidence

> **Stage:** Verify · **Owner:** P7
> **Prev:** [10 · Edge Cases](10-edge-cases.md) · **Next:** [12 · Iteration Log](12-iteration-log.md)

> ⚠️ **Template: no results recorded yet.** Only paste output you actually ran. Never write "passes" for a test that wasn't executed.

---

## 1. Automated tests
**Command (from the project root):** `python -m pytest -v`
**Run at:** _(time)_ · **Commit:** _(git hash)_ · **Result:** _(N passed / M failed)_
```
(paste the real pytest -v output here)
```

## 2. Rule coverage (every BR has at least one test)
| Rule | Test(s) | Result |
|---|---|---|
| BR1 | | |
| BR2 | | |
| BR3 | | |
| BR4 | | |
| BR5 | | |
| BR6 | | |
| BR7 | | |
| BR8 | | |
| BR9 | | |
| BR10 | | |

Planned test names per edge case are in [10 · Edge Cases](10-edge-cases.md).

## 3. Already verified during the contract phase
Run against `src/lms/persistence/schema.sql` in an in-memory SQLite DB (see [12 · I-4](12-iteration-log.md)):
- Overlapping active insert on the same copy → aborted `COPY_OVERLAP`
- Adjacent dates (ends 04, next starts 05) → allowed
- Cancelled overlapping row → allowed (doesn't block)
- Re-activating a cancelled row that overlaps → aborted `COPY_OVERLAP`
- `end_date < start_date` → `CHECK constraint failed`

These must be re-proven as pytest tests (`test_trigger_*`) so they run on every change.

## 4. Manual demo checklist ([06 · PRD §5](06-prd.md#5-acceptance-criteria-demo-scenarios))
| # | Scenario | Pass/Fail | Notes |
|---|---|---|---|
| 1 | Happy path: request → approve → issue → return | | |
| 2 | Conflict: Design Patterns, ravi refused + `DUPLICATE_REQUEST` case | | |
| 3 | Restricted copy: only DP-1 is offered | | |
| 4 | Reject releases the copy | | |
| 5 | Cancel releases the copy | | |
| 6 | Damaged on return → booking moved / closed | | |
| 7 | Invalid input: past start, 31 days, end < start | | |
