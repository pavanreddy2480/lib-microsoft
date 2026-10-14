"""Adapter: LibrarianPort -> the real services and repository.

The only place in the librarian UI that touches `lending`, `repo`, `db`, `seed`
and `clock`. It joins ids to names so the pages receive ready-to-show rows.
"""
from __future__ import annotations

from contextlib import closing
from datetime import date
from typing import Sequence

from lms.domain import clock
from lms.domain.models import AffectedRequest, CopyStatus, Event, Request, RequestStatus, User
from lms.persistence import db, seed
from lms.persistence import repository as repo
from lms.services import lending
from lms.ui.librarian import presenters
from lms.ui.librarian.views import AffectedRow, CopyRow, RequestRow, ReturnOutcome


def _affected_rows(items: Sequence[AffectedRequest]) -> list[AffectedRow]:
    return [AffectedRow(a.request_id, a.outcome, a.message) for a in items]


class ServicePort:
    # ---- reads ----
    def today(self) -> date:
        return clock.business_today()

    def requests(self, statuses: Sequence[RequestStatus] | None = None) -> list[RequestRow]:
        with closing(db.get_conn()) as conn:
            raw = repo.list_requests(conn, statuses=statuses)
            return self._rows(conn, raw)

    def inventory(self) -> list[CopyRow]:
        with closing(db.get_conn()) as conn:
            titles = {t.id: t.title for t in repo.list_titles(conn)}
            members = {m.id: m.full_name for m in repo.list_members(conn)}
            rows = []
            for copy in repo.list_copies(conn):
                commitments = repo.active_commitments_for_copy(conn, copy.id)
                rows.append(CopyRow(
                    id=copy.id, title=titles.get(copy.title_id, "?"),
                    copy_code=copy.copy_code, status=copy.status, note=copy.note,
                    commitment=presenters.describe_commitment(
                        commitments, lambda r: members.get(r.member_id, "?")),
                ))
            return rows

    def history(self, request_id: int) -> list[Event]:
        return lending.get_request_history(request_id)

    # ---- commands ----
    def approve(self, actor: User, request_id: int, note: str = "") -> RequestRow:
        return self._one(lending.approve_request(actor, request_id, note))

    def reject(self, actor: User, request_id: int, reason: str) -> RequestRow:
        return self._one(lending.reject_request(actor, request_id, reason))

    def cancel(self, actor: User, request_id: int, note: str = "") -> RequestRow:
        return self._one(lending.cancel_request(actor, request_id, note))

    def issue(self, actor: User, request_id: int) -> RequestRow:
        return self._one(lending.issue_loan(actor, request_id))

    def return_loan(self, actor: User, request_id: int,
                    condition: CopyStatus = CopyStatus.IN_SERVICE,
                    note: str = "") -> ReturnOutcome:
        request, affected = lending.return_loan(actor, request_id, condition, note)
        return ReturnOutcome(self._one(request), tuple(_affected_rows(affected)))

    def set_copy_status(self, actor: User, copy_id: int, status: CopyStatus,
                        note: str = "") -> list[AffectedRow]:
        return _affected_rows(lending.set_copy_status(actor, copy_id, status, note))

    def reset_demo(self) -> None:
        seed.reset_db()
        clock.reset_business_today()

    # ---- helpers ----
    def _one(self, request: Request) -> RequestRow:
        with closing(db.get_conn()) as conn:
            return self._rows(conn, [request])[0]

    @staticmethod
    def _rows(conn, requests: Sequence[Request]) -> list[RequestRow]:
        members = {m.id: m.full_name for m in repo.list_members(conn)}
        titles = {t.id: t.title for t in repo.list_titles(conn)}
        copies = {c.id: c.copy_code for c in repo.list_copies(conn)}
        return [
            RequestRow(
                id=r.id, member_name=members.get(r.member_id, "?"),
                title=titles.get(r.title_id, "?"), copy_code=copies.get(r.copy_id, "?"),
                start_date=r.start_date, end_date=r.end_date, status=r.status,
                created_at=r.created_at, decision_note=r.decision_note,
            )
            for r in requests
        ]
