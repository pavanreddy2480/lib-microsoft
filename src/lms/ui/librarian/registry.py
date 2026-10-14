"""Where pages obtain their port (Service Locator with an override seam).

Production: lazily builds the real `ServicePort`. Tests call `set_port(fake)` /
`reset_port()` to inject a double, which is what makes page-level (AppTest)
end-to-end tests possible without a database.
"""
from __future__ import annotations

from lms.ui.librarian.port import LibrarianPort

_port: LibrarianPort | None = None


def get_port() -> LibrarianPort:
    global _port
    if _port is None:
        from lms.ui.librarian.service_port import ServicePort  # lazy: keeps imports light
        _port = ServicePort()
    return _port


def set_port(port: LibrarianPort | None) -> None:
    global _port
    _port = port


def reset_port() -> None:
    set_port(None)
