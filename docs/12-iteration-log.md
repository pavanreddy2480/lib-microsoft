# 12 · Iteration Log (decisions, corrections, AI usage)

> **Stage:** Iterate · **Owner:** P1 (keeps it current). **Everyone adds entries.**
> **Prev:** [11 · Test Evidence](11-test-evidence.md) · **Next:** [13 · Pitch](13-pitch.md)

The evaluators score **how we directed, questioned and validated AI**, not how much code it produced. This log is the evidence. Every entry is something that actually happened, with how it was verified. **Never add an entry for something that wasn't run or checked.**

---

## 1. How we used AI
```
  HUMAN decides           AI proposes / drafts            BOTH verify
  -------------           --------------------            -----------
  scope, policies   --->  options + recommended default  ---> run it (tests, in-memory DB,
  (4 decision Qs)         contract, stubs, docs                 AppTest, grep checks)
         ^                                                          |
         +---------------- corrections fed back <------------------+
```
- The AI asked for decisions **before** building, and the team overrode its recommendation twice (see I-2).
- Every factual claim was **executed** before it was trusted: trigger behaviour, imports, page loading, paths.
- Two AI sessions worked in parallel, and **cross-reviewed each other**, catching a bug the author missed (I-12).

## 2. Log
| # | Time (14 Oct) | What happened | Who | How it was verified / outcome |
|---|---|---|---|---|
| I-1 | 16:52 → | Read the PDF. Noticed the seed data is dated **Aug 2026** while the machine date is **14 Oct 2026**, so all seeded loans would be overdue. | AI flagged, team decided | Became decision A3: configurable business date, default 2026-08-01 |
| I-2 | before 17:20 | The AI asked 4 decision questions, each with a recommended default. The team accepted 2 and **overrode 2**: **simple login** instead of no-login, and **30-day** max instead of the 14 days the AI recommended. | Team | Recorded as A4 and A11 in [04](04-assumptions-and-scope.md) |
| I-3 | before 17:20 | Database choice. Team rule: "write-intensive → Postgres, else SQLite; no Postgres → SQLite". Checked the machine: `psql`/`postgres` aren't installed, and the workload is mostly reads. | AI checked, team rule | **SQLite** (T1 in [07](07-architecture.md)) |
| I-4 | 17:20 `72bdf76` | Contract-first scaffold: state model, schema, error codes, stubs, 7 task files. | AI drafted | The overlap trigger was **run** in an in-memory DB: overlap blocked, adjacent dates allowed, a cancelled row doesn't block, re-activating an overlap is blocked, the end<start CHECK fires |
| I-5 | 17:20 | **AI self-correction:** the expected-results table for P3 said *AI: A Modern Approach* on 06 Aug has **1** free copy. Re-deriving it gives **2**, because AIMA-1's loan ends 04 Aug. | AI | Fixed in `team/3.md` before the commit |
| I-6 | 17:20 | `streamlit.exe` isn't on PATH on this machine | Found by running it | All docs use `python -m streamlit` / `python -m pytest` |
| I-7 | 17:25 `ab1fd3e` | Restructured into a `src/` layered package. **AppTest revealed** that every page crashed with `No module named 'ui_common'` unless launched through Home.py (it relied on Streamlit's sys.path behaviour). | Found by test | Moved to `lms.ui.common`. All 6 pages re-tested: they load and show the login guard. |
| I-8 | 17:25 | **Layering violation:** `persistence/seed.py` imported `hash_password` from `services/auth.py` (an upward dependency). | AI review | Moved to `domain/security.py`. A grep check confirms no upward imports. |
| I-9 | 17:25 | **AI tooling bug:** a bulk rename script (`services.` → `lending.`) also changed the prose "No external services." into "No external lending." | Caught by a review grep | Fixed in [06](06-prd.md). Lesson: review regex-based bulk edits. |
| I-10 | 17:20 | The contract changed `submit_request(member_id, …)` to `submit_request(actor, …)`, so role checks live in the **backend**, not just the UI. | AI proposed, noted to team | T-decision in [07 §11](07-architecture.md#11-security-model-prototype) |
| I-11 | 17:29 `35333ed` | `CONTEXT.md` onboarding brief, so every teammate (and their AI) starts with the same rules | AI drafted | Links and API signatures checked against the code by script |
| I-12 | 17:35-17:45 | **Two AI sessions in one working tree** (P1 session and docs session). They agreed by message on: file ownership, pathspec-only commits, no branch switching. P1's `ASSUMPTIONS.md` "Enforced in" column was merged into [04](04-assumptions-and-scope.md), and `BRD.md` was split into 01-04. | Both sessions | `dff114a` (P1) and the docs commit didn't touch each other's files |
| I-13 | 17:45 | **Cross-review catch (by P1 session):** the planned demo/test "two members take the free Clean Code copies, the third is refused with NO_COPY_AVAILABLE" is **impossible with the seed users**. The only remaining members (asha, ravi) already hold Clean Code loans, so they hit `DUPLICATE_REQUEST` first. | P1 session found it, docs session verified it against the seed | The demo moved to *Design Patterns* (meera 05-10, ravi 07-08 refused, next free 11 Aug). The multi-copy test moved to *Intro to Algorithms* with kiran. Fixed in CONTEXT, 02, 06, 10, team/5, team/7. |
| I-14 | 17:45 | The edge-case review ([10](10-edge-cases.md)) found **5 cases the contract doesn't specify** (O1-O5), e.g. approving a request whose dates have already passed | AI review | Raised as open decisions for P4, not silently decided |

## 3. Add your entries
Use the same columns. Good entries are specific and verifiable:
```
| I-15 | 18:05 | AI suggested computing availability with a title-level counter;
|      |       | rejected because it breaks BR2 (copy-level) | P3 | test_free_counts_match_per_copy passes |
```
Things worth logging:
- AI suggestions you **rejected**, and why
- Bugs found by tests or by review (whether in AI code or ours)
- Contract changes (who asked, what changed, who was told)
- Decisions on the open edge cases O1-O5
