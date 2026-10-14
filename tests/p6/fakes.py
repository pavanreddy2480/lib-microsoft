"""In-memory LibrarianPort used by the librarian-UI tests.

It mirrors the documented service contract (docs/CONTEXT.md §5) only as far as the UI
can observe it: legal transitions, REASON_REQUIRED, ISSUE_NOT_ALLOWED, and the
"move or close" policy when a copy goes out of service. `test_port_contract.py` runs the
same assertions against this fake and the real adapter, so the fake cannot drift unnoticed.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Sequence

from lms.domain import clock
from lms.domain.errors import (
    INVALID_TRANSITION, ISSUE_NOT_ALLOWED, NOT_AUTHORIZED, NOT_FOUND, REASON_REQUIRED,
    BusinessRuleError,
)
from lms.domain.models import (
    ACTIVE_STATUSES, CopyStatus, Event, RequestStatus, Role, User, can_transition,
)
from lms.ui.librarian.views import AffectedRow, CopyRow, RequestRow, ReturnOutcome

D = date

# (title, [copy codes])
TITLES = {
    "Clean Code": ["CC-1", "CC-2", "CC-3", "CC-4"],
    "Introduction to Algorithms": ["ITA-1", "ITA-2", "ITA-3"],
    "Design Patterns": ["DP-1", "DP-2"],
    "Database System Concepts": ["DSC-1", "DSC-2", "DSC-3", "DSC-4", "DSC-5"],
    "Artificial Intelligence: A Modern Approach": ["AIMA-1", "AIMA-2", "AIMA-3"],
}


class InMemoryPort:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.reset_count = 0
        self._copies: dict[str, dict] = {}
        for title, codes in TITLES.items():
            for code in codes:
                self._copies[code] = {"title": title, "status": CopyStatus.IN_SERVICE, "note": ""}
        self._copies["DP-2"]["status"] = CopyStatus.DAMAGED
        self._rows: list[RequestRow] = []
        self._events: dict[int, list[Event]] = {}
        self._seed_rows()

    # ---- seed (mirrors the problem-statement data + two pending requests) ----
    def _seed_rows(self) -> None:
        self._add("Asha Rao", "Database System Concepts", "DSC-1", D(2026, 8, 5), D(2026, 8, 12), RequestStatus.PENDING)
        self._add("Ravi Kumar", "Design Patterns", "DP-1", D(2026, 8, 6), D(2026, 8, 9), RequestStatus.PENDING)
        self._add("Meera Iyer", "Introduction to Algorithms", "ITA-1", D(2026, 8, 4), D(2026, 8, 8), RequestStatus.RESERVED)
        self._add("Asha Rao", "Artificial Intelligence: A Modern Approach", "AIMA-2", D(2026, 8, 6), D(2026, 8, 7), RequestStatus.RESERVED)
        self._add("Asha Rao", "Clean Code", "CC-1", D(2026, 7, 21), D(2026, 8, 4), RequestStatus.ISSUED)
        self._add("Kiran Das", "Artificial Intelligence: A Modern Approach", "AIMA-1", D(2026, 7, 21), D(2026, 8, 4), RequestStatus.ISSUED)
        # A future reservation on AIMA-1 (the PRD "damaged on return" scenario).
        self._add("Asha Rao", "Artificial Intelligence: A Modern Approach", "AIMA-1", D(2026, 8, 10), D(2026, 8, 12), RequestStatus.RESERVED)

    def _add(self, member, title, code, start, end, status) -> RequestRow:
        row = RequestRow(len(self._rows) + 1, member, title, code, start, end, status,
                         "2026-07-30 10:00:00")
        self._rows.append(row)
        self._events[row.id] = []
        return row

    # ---- reads ----
    def today(self) -> date:
        return clock.business_today()

    def requests(self, statuses: Sequence[RequestStatus] | None = None) -> list[RequestRow]:
        rows = [r for r in self._rows if statuses is None or r.status in set(statuses)]
        return sorted(rows, key=lambda r: r.id, reverse=True)

    def inventory(self) -> list[CopyRow]:
        out = []
        for i, (code, c) in enumerate(self._copies.items(), start=1):
            active = sorted((r for r in self._rows
                             if r.copy_code == code and r.status in ACTIVE_STATUSES),
                            key=lambda r: (r.start_date, r.id))
            text = ""
            if active:
                r = active[0]
                text = f"{r.status.value} {r.start_date:%d %b %Y} → {r.end_date:%d %b %Y} ({r.member_name})"
            out.append(CopyRow(i, c["title"], code, c["status"], c["note"], text))
        return out

    def history(self, request_id: int) -> list[Event]:
        return list(self._events.get(request_id, []))

    # ---- commands ----
    def approve(self, actor: User, request_id: int, note: str = "") -> RequestRow:
        self.calls.append(("approve", request_id, note))
        return self._move(actor, request_id, RequestStatus.RESERVED, note, "approve")

    def reject(self, actor: User, request_id: int, reason: str) -> RequestRow:
        self.calls.append(("reject", request_id, reason))
        if not reason.strip():
            raise BusinessRuleError(REASON_REQUIRED, "A rejection reason is required.")
        return self._move(actor, request_id, RequestStatus.REJECTED, reason, "reject")

    def cancel(self, actor: User, request_id: int, note: str = "") -> RequestRow:
        self.calls.append(("cancel", request_id, note))
        return self._move(actor, request_id, RequestStatus.CANCELLED, note, "cancel")

    def issue(self, actor: User, request_id: int) -> RequestRow:
        self.calls.append(("issue", request_id))
        row = self._get(request_id)
        if self.today() < row.start_date:
            raise BusinessRuleError(
                ISSUE_NOT_ALLOWED, f"Cannot issue before the start date ({row.start_date:%d %b %Y}).")
        return self._move(actor, request_id, RequestStatus.ISSUED, "", "issue")

    def return_loan(self, actor: User, request_id: int,
                    condition: CopyStatus = CopyStatus.IN_SERVICE, note: str = "") -> ReturnOutcome:
        self.calls.append(("return", request_id, condition, note))
        row = self._move(actor, request_id, RequestStatus.RETURNED, note, "return")
        affected: list[AffectedRow] = []
        if condition is not CopyStatus.IN_SERVICE:
            self._copies[row.copy_code]["status"] = condition
            affected = self._out_of_service(row.copy_code)
        return ReturnOutcome(row, tuple(affected))

    def set_copy_status(self, actor: User, copy_id: int, status: CopyStatus,
                        note: str = "") -> list[AffectedRow]:
        self.calls.append(("set_copy_status", copy_id, status, note))
        code = list(self._copies)[copy_id - 1]
        self._copies[code]["status"] = status
        self._copies[code]["note"] = note
        return self._out_of_service(code) if status is not CopyStatus.IN_SERVICE else []

    def reset_demo(self) -> None:
        self.reset_count += 1

    # ---- internals ----
    def _get(self, request_id: int) -> RequestRow:
        for r in self._rows:
            if r.id == request_id:
                return r
        raise BusinessRuleError(NOT_FOUND, f"Request #{request_id} not found.")

    def _replace(self, row: RequestRow, **changes) -> RequestRow:
        new = replace(row, **changes)
        self._rows[self._rows.index(row)] = new
        return new

    def _move(self, actor: User, request_id: int, target: RequestStatus, note: str, verb: str) -> RequestRow:
        if actor.role is not Role.LIBRARIAN:
            raise BusinessRuleError(NOT_AUTHORIZED, f"Only librarians can {verb} requests.")
        row = self._get(request_id)
        if not can_transition(row.status, target):
            raise BusinessRuleError(
                INVALID_TRANSITION, f"Cannot {verb} a request that is {row.status.value}.")
        self._events[request_id].append(
            Event(len(self._events[request_id]) + 1, request_id, row.status.value, target.value,
                  actor.username, note, "2026-08-01 09:00:00"))
        return self._replace(row, status=target, decision_note=note or row.decision_note)

    def _out_of_service(self, code: str) -> list[AffectedRow]:
        """Move future PENDING/RESERVED commitments to another free copy, else close them."""
        out: list[AffectedRow] = []
        for row in [r for r in self._rows if r.copy_code == code
                    and r.status in (RequestStatus.PENDING, RequestStatus.RESERVED)]:
            replacement = self._free_copy(row, exclude=code)
            if replacement:
                self._replace(row, copy_code=replacement)
                out.append(AffectedRow(row.id, "MOVED", f"moved from {code} to {replacement}"))
            else:
                closed = (RequestStatus.REJECTED if row.status is RequestStatus.PENDING
                          else RequestStatus.CANCELLED)
                msg = f"Copy {code} became unavailable and no other copy is free for these dates."
                self._replace(row, status=closed, decision_note=msg)
                out.append(AffectedRow(row.id, "CLOSED", msg))
        return out

    def _free_copy(self, row: RequestRow, exclude: str) -> str | None:
        for code, c in self._copies.items():
            if code == exclude or c["title"] != row.title or c["status"] is not CopyStatus.IN_SERVICE:
                continue
            busy = any(r.copy_code == code and r.status in ACTIVE_STATUSES
                       and r.start_date <= row.end_date and row.start_date <= r.end_date
                       for r in self._rows if r.id != row.id)
            if not busy:
                return code
        return None
