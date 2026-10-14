# 09 · Development Plan

> **Stage:** Build · **Owner:** P1 (integration lead)
> **Prev:** [08 · Code Structure](08-code-structure.md) · **Next:** [10 · Edge Cases](10-edge-cases.md)

How 7 people build this in 90 minutes without blocking or overwriting each other.

---

## 1. Strategy: contract first, then parallel
```
  Phase 0 (done)               Phase 1 (parallel)                 Phase 2           Phase 3
  CONTRACT                     BUILD                              INTEGRATE         SHIP
  +---------------+    +--> P2 persistence -+
  | models, errors|    +--> P3 availability -+--> P4 services --+
  | schema, config|----+                                        +--> merge --> tests --> demo
  | stubs, docs   |    +--> P5 member UI (fake data first) -----+    green      + pitch
  +---------------+    +--> P6 librarian UI (fake data first) --+
                       +--> P7 tests (written against the contract)
                       +--> P1 docs, login shell, pitch
```
Everyone starts at T+15 because the **signatures already exist**. Until real code lands, UI developers use hard-coded dataclasses and P7 writes tests that are expected to fail.

## 2. Work breakdown
| Person | Deliverable | Depends on | Unblocks | Task file |
|---|---|---|---|---|
| P1 | Login shell, docs, pitch, merges | contract | everyone (merges) | [team/1.md](team/1.md) |
| P2 | `db.py`, `repository.py`, `auth.py` | contract | P3, P4, P5, P6, P7 | [team/2.md](team/2.md) |
| P3 | `availability.py`, `seed.py` | P2 signatures | P4, P5, P7 | [team/3.md](team/3.md) |
| P4 | `lending.py` | P2 + P3 | P5, P6, P7 | [team/4.md](team/4.md) |
| P5 | Catalog, My Requests pages | P4 signatures | demo | [team/5.md](team/5.md) |
| P6 | Review Queue, Loans, Inventory pages | P4 signatures | demo | [team/6.md](team/6.md) |
| P7 | Tests, architecture upkeep, test evidence, bonus | contract | confidence | [team/7.md](team/7.md) |

## 3. Critical path
```
   P2 persistence (T+15 -> T+35) --+
                                   +--> P4 lending (-> T+50) --> P5/P6 wired (-> T+55) --> tests green (-> T+70)
   P3 availability (T+15 -> T+35) -+
```
If P2 or P3 slips, everything slips. **Help them first** if you finish early.

## 4. Timeline (90 minutes)
```
 minute:   0    10    20    30    40    50    60    70    80    90
           |-----|-----|-----|-----|-----|-----|-----|-----|-----|
 Contract  #######                                                     (done)
 P2        .     ################                                       merge by T+35
 P3        .     ################                                       merge by T+35
 P4        .     .......###################                             merge by T+50
 P5 / P6   .     ##########(fake data)######(real)####                  ready by T+55
 P7        .     ##########(tests vs contract)#######......####         green by T+70
 P1        .     ####(Home)######(docs)######(merging)########(pitch)##
 Integrate                                   ############                T+55 -> T+70
 Fix+Evid.                                               ######          T+70 -> T+80
 Rehearse                                                      ######    T+80 -> T+90
```

## 5. Git workflow
```
 main  o---------------------------o-----------o-----------o-------o----->  (always runnable)
        \                         /           /           /       /
 p2-persistence  o---o---o-------+           /           /       /
 p3-availability    o---o---o---------------+           /       /
 p4-services             o---o---o---o-----------------+       /
 p5-member-ui / p6-librarian-ui   o---o---o---o---o-----------+
```
- **Branches:** `p1-docs-shell`, `p2-persistence`, `p3-availability`, `p4-services`, `p5-member-ui`, `p6-librarian-ui`, `p7-tests`
- **Merge order (by P1):** P2 → P3 → P4 → P5/P6 → P7. After each merge, run `python -m pytest` and `python -m streamlit run app/Home.py`.
- **Commits:** small, meaningful messages ("availability: inclusive overlap + validate_period"). The judges look at history per person.
- **Never** commit `data/`, `.venv/` or `__pycache__/`. Never force-push `main`.
- **Same machine, several sessions or people?** Commit with an explicit pathspec (`git commit -- path/to/your/files`) so you don't sweep in someone else's staged changes.

## 6. Communication protocol
| Situation | Do this |
|---|---|
| You need a contract change | Ask P1, who announces it. One person changes it in its own commit. |
| You are blocked | Say so immediately in the team chat, and code against the signature with fake data |
| You finished early | Help the critical path (P2, P3, P4), then write tests |
| A test of yours fails because of someone else's code | Tell the owner the test name and the error; don't fix their file yourself |

## 7. Definition of done (for every task)
- [ ] No `NotImplementedError` left in your files
- [ ] Your checklist in `docs/team/N.md` is ticked
- [ ] `python -m pytest` shows no new failures from your area
- [ ] The app starts and your page or feature works by hand
- [ ] Committed on your branch with clear messages, and merged by P1
- [ ] You can explain your code, one business rule, one trade-off, and how you validated it

## 8. Integration checklist (P1, T+55 → T+70)
- [ ] `pip install -r requirements.txt` on a clean clone works
- [ ] `python -m lms.persistence.seed` → "Database reset and seeded."
- [ ] `python -m pytest` green → paste the output into [11-test-evidence.md](11-test-evidence.md)
- [ ] Walk the 7 acceptance scenarios in [06 · PRD §5](06-prd.md#5-acceptance-criteria-demo-scenarios)
- [ ] Reset the demo data before presenting
