# Architecture

This document describes the agreed contracts. Service and persistence implementations are still pending; diagrams do not establish that runtime behavior passes validation.

## Layers

```mermaid
flowchart TD
    Pages[Streamlit Home and pages] --> UI[lms.ui.common]
    UI --> Services[lms.services.lending and auth]
    Services --> Availability[lms.services.availability]
    Services --> Repo[lms.persistence.repository]
    Availability --> Repo
    Repo --> SQLite[(SQLite tables and overlap triggers)]
    Services --> Transactions[lms.persistence.db transactions]
    Transactions --> SQLite
```

Pages also call service/read helpers directly. Shared dataclasses and enums live in `src/lms/domain/models.py`; errors in `errors.py`; the controllable business date in `clock.py`. Writes use a single `BEGIN IMMEDIATE` transaction, with rollback on exceptions. Tests use temporary databases, not the application database.

## Request state machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: submit
    PENDING --> RESERVED: librarian approves
    PENDING --> REJECTED: reject with reason / no replacement
    PENDING --> CANCELLED: withdraw
    RESERVED --> ISSUED: issue within inclusive dates
    RESERVED --> CANCELLED: cancel / no replacement
    ISSUED --> RETURNED: return with condition
    REJECTED --> [*]
    CANCELLED --> [*]
    RETURNED --> [*]
```

PENDING, RESERVED, and ISSUED hold a copy. Moving a request to a replacement copy preserves its status and writes an audit event. Terminal states cannot reopen. Only IN_SERVICE copies can be allocated.

## Data relationships

```mermaid
erDiagram
    users ||--o{ requests : borrows
    titles ||--o{ copies : has
    titles ||--o{ requests : requested
    copies ||--o{ requests : allocated
    requests ||--o{ request_events : records
    users {
        int id PK
        string username UK
        string password_hash
        string role
    }
    titles {
        int id PK
        string title UK
        string category
    }
    copies {
        int id PK
        int title_id FK
        string copy_code UK
        string status
    }
    requests {
        int id PK
        int member_id FK
        int title_id FK
        int copy_id FK
        date start_date
        date end_date
        string status
        string decision_note
        string issued_at
        string returned_at
    }
    request_events {
        int id PK
        int request_id FK
        string from_status
        string to_status
        string actor
        string note
        string at
    }
```

Event actor is a username stored as text, not a user foreign key.

## Rule ownership

| Rule | Enforcement contract |
|---|---|
| BR1 | `services/lending.py: submit_request`; `persistence/schema.sql` required fields and foreign keys |
| BR2 | `services/availability.py: is_copy_free, free_copies, check_availability` |
| BR3 | Inclusive `overlaps`; transactional submission; schema insert/update overlap triggers |
| BR4 | `submit_request` rejects without inserting when no copy is free |
| BR5 | Availability checks copy status; lending inventory and return handlers manage affected commitments |
| BR6 | Submission creates PENDING; approval and issue enforce `domain/models.py` transitions |
| BR7 | Reject requires reason, releases commitment, and closes request; no edit API |
| BR8 | Cancellation allowed before issue; owning member or librarian only |
| BR9 | Return closes issued loan; condition can exclude copy and move/close future commitments |
| BR10 | Availability must cover entire interval on one copy; no partial allocation or alternative-title API |

Dates are inclusive and borrowing is limited to 30 inclusive days. Overdue issued loans use `max(end_date, business_today())` in availability. The SQL triggers check stored date ranges only, so overdue extension is enforced by the service, not independently by the triggers. `next_free_date` is a contract-defined hint based on blocking commitment end dates, not a guarantee that a complete future interval is free.
