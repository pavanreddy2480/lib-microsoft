# Library Management System: IIIT Hackathon

A Streamlit + SQLite prototype of a university library lending lifecycle:
**request → review → confirmed reservation → loan → return**, with copy-level availability that never double-books a physical copy.

> Status: interface contract and task split are done; implementation is in progress. Person 1 completes this README (see `tasks/1.md`).

## Run
```bash
pip install -r requirements.txt     # Python 3.10+
python -m streamlit run app.py      # http://localhost:8501 (streamlit.exe may not be on PATH)
python -m pytest -q
python -m lms.seed                  # reset + reseed the demo DB (data/library.db)
```
Demo logins: `librarian / lib123`, and members `asha`, `ravi`, `meera`, `kiran` with password `pass123`.

## Layout
```
app.py, ui_common.py, pages/   Streamlit UI (login, member pages, librarian pages)
lms/models.py                  single state model (enums, transitions, dataclasses)   [contract]
lms/errors.py, clock.py        error codes, business date                            [contract]
lms/schema.sql                 SQLite schema + no-overlap trigger                    [contract]
lms/db.py, repo.py, auth.py    persistence + login
lms/availability.py, seed.py   copy-level availability engine + PDF seed data
lms/services.py                lifecycle state machine (submit/approve/reject/cancel/issue/return)
tests/                         pytest suite
docs/                          BRD, PRD, assumptions, architecture, test evidence, pitch
tasks/1.md … 7.md              per-person work split
```

## Docs
[BRD](docs/BRD.md) · [PRD](docs/PRD.md) · ASSUMPTIONS · ARCHITECTURE · TEST_EVIDENCE · PITCH (to be written by their owners)
