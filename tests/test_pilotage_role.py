import pytest

from mcp_clickhouse_lite import mcp_server
from mcp_clickhouse_lite.mcp_server import (
    PILOTAGE_ROLE_DRH,
    PILOTAGE_ROLE_HEADER,
    PILOTAGE_ROLE_PUBLIC,
    resolve_pilotage_role,
)


def test_resolve_pilotage_role_defaults_to_public_with_no_request_context():
    """Outside a live HTTP request (e.g. background task), get_http_headers() returns {}."""
    assert resolve_pilotage_role() == PILOTAGE_ROLE_PUBLIC


def test_resolve_pilotage_role_reads_drh_header(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        mcp_server, "get_http_headers", lambda: {PILOTAGE_ROLE_HEADER.lower(): PILOTAGE_ROLE_DRH}
    )
    assert resolve_pilotage_role() == PILOTAGE_ROLE_DRH


def test_resolve_pilotage_role_reads_public_header(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        mcp_server,
        "get_http_headers",
        lambda: {PILOTAGE_ROLE_HEADER.lower(): PILOTAGE_ROLE_PUBLIC},
    )
    assert resolve_pilotage_role() == PILOTAGE_ROLE_PUBLIC


def test_resolve_pilotage_role_falls_back_to_public_on_unknown_value(
    monkeypatch: pytest.MonkeyPatch,
):
    """Fail closed: an unrecognized role value never grants the elevated role."""
    monkeypatch.setattr(
        mcp_server, "get_http_headers", lambda: {PILOTAGE_ROLE_HEADER.lower(): "admin"}
    )
    assert resolve_pilotage_role() == PILOTAGE_ROLE_PUBLIC


def test_resolve_pilotage_role_falls_back_to_public_when_header_absent(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(mcp_server, "get_http_headers", lambda: {})
    assert resolve_pilotage_role() == PILOTAGE_ROLE_PUBLIC
