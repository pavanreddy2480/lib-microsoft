"""Unit tests: the port registry seam."""
from lms.ui.librarian import registry


def test_set_and_reset_port(fake_port):
    assert registry.get_port() is fake_port
    registry.reset_port()
    assert registry._port is None


def test_default_port_is_the_real_adapter():
    from lms.ui.librarian.service_port import ServicePort
    assert isinstance(registry.get_port(), ServicePort)
    assert registry.get_port() is registry.get_port()  # cached
