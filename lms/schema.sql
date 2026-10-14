-- CONTRACT FILE. SQLite schema for the Library Management System.
-- Dates are stored as ISO text 'YYYY-MM-DD' (string comparison == date comparison).
-- Timestamps (created_at, issued_at, ...) are ISO text 'YYYY-MM-DD HH:MM:SS'.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('MEMBER', 'LIBRARIAN'))
);

CREATE TABLE IF NOT EXISTS titles (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS copies (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title_id  INTEGER NOT NULL REFERENCES titles(id),
    copy_code TEXT NOT NULL UNIQUE,
    status    TEXT NOT NULL DEFAULT 'IN_SERVICE'
              CHECK (status IN ('IN_SERVICE', 'DAMAGED', 'UNDER_REPAIR', 'LOST',
                                'REFERENCE_ONLY', 'RESTRICTED')),
    note      TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS requests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id     INTEGER NOT NULL REFERENCES users(id),
    title_id      INTEGER NOT NULL REFERENCES titles(id),
    copy_id       INTEGER NOT NULL REFERENCES copies(id),
    start_date    TEXT NOT NULL,
    end_date      TEXT NOT NULL,
    status        TEXT NOT NULL
                  CHECK (status IN ('PENDING', 'RESERVED', 'ISSUED',
                                    'RETURNED', 'REJECTED', 'CANCELLED')),
    created_at    TEXT NOT NULL,
    decision_note TEXT NOT NULL DEFAULT '',
    issued_at     TEXT,
    returned_at   TEXT,
    CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_requests_copy   ON requests(copy_id, status);
CREATE INDEX IF NOT EXISTS idx_requests_member ON requests(member_id, status);

CREATE TABLE IF NOT EXISTS request_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id  INTEGER NOT NULL REFERENCES requests(id),
    from_status TEXT,
    to_status   TEXT NOT NULL,
    actor       TEXT NOT NULL,
    note        TEXT NOT NULL DEFAULT '',
    at          TEXT NOT NULL
);

-- Defense in depth for rule R3: a copy can never hold two overlapping ACTIVE
-- commitments, even if application code has a bug. Overlap uses inclusive dates.
-- (Overdue ISSUED loans extending past end_date are handled in availability.py.)
CREATE TRIGGER IF NOT EXISTS trg_no_overlap_insert
BEFORE INSERT ON requests
WHEN NEW.status IN ('PENDING', 'RESERVED', 'ISSUED')
BEGIN
    SELECT RAISE(ABORT, 'COPY_OVERLAP')
    WHERE EXISTS (
        SELECT 1 FROM requests r
        WHERE r.copy_id = NEW.copy_id
          AND r.status IN ('PENDING', 'RESERVED', 'ISSUED')
          AND r.start_date <= NEW.end_date
          AND NEW.start_date <= r.end_date
    );
END;

CREATE TRIGGER IF NOT EXISTS trg_no_overlap_update
BEFORE UPDATE OF copy_id, status, start_date, end_date ON requests
WHEN NEW.status IN ('PENDING', 'RESERVED', 'ISSUED')
BEGIN
    SELECT RAISE(ABORT, 'COPY_OVERLAP')
    WHERE EXISTS (
        SELECT 1 FROM requests r
        WHERE r.id <> NEW.id
          AND r.copy_id = NEW.copy_id
          AND r.status IN ('PENDING', 'RESERVED', 'ISSUED')
          AND r.start_date <= NEW.end_date
          AND NEW.start_date <= r.end_date
    );
END;
