"""The port the librarian pages depend on (Dependency Inversion).

Pages and presenters know this Protocol, never `lending`/`repo` directly. The real
implementation is `service_port.ServicePort`; tests plug in an in-memory fake that
must satisfy the same contract tests.
"""
from __future__ import annotations

from datetime import date
from typing import Protocol, Sequence

from lms.domain.models import CopyStatus, Event, RequestStatus, User
from lms.ui.librarian.views import CopyRow, AffectedRow, RequestRow, ReturnOutcome


class LibrarianPort(Protocol):
    # ---- reads ----
    def today(self) -> date: ...
    def requests(self, statuses: Sequence[RequestStatus] | None = None) -> list[RequestRow]:
        """Rows for the given statuses (all when None), newest first."""
    def inventory(self) -> list[CopyRow]: ...
    def history(self, request_id: int) -> list[Event]: ...

    # ---- librarian commands (raise BusinessRuleError on rule violations) ----
    def approve(self, actor: User, request_id: int, note: str = "") -> RequestRow: ...
    def reject(self, actor: User, request_id: int, reason: str) -> RequestRow: ...
    def cancel(self, actor: User, request_id: int, note: str = "") -> RequestRow: ...
    def issue(self, actor: User, request_id: int) -> RequestRow: ...
    def return_loan(self, actor: User, request_id: int,
                    condition: CopyStatus = CopyStatus.IN_SERVICE,
                    note: str = "") -> ReturnOutcome: ...
    def set_copy_status(self, actor: User, copy_id: int, status: CopyStatus,
                        note: str = "") -> list[AffectedRow]: ...
    def reset_demo(self) -> None: ...
