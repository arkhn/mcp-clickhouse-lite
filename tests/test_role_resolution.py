from dataclasses import dataclass

import pytest

from mcp_clickhouse_lite import mcp_server
from mcp_clickhouse_lite.mcp_server import CLICKHOUSE_ROLE_HEADER, resolve_role


@dataclass
class _FakeMCPConfig:
    accepted_roles: frozenset[str]
    default_role: str | None


def _patch_mcp_config(
    monkeypatch: pytest.MonkeyPatch, accepted_roles: frozenset[str], default_role: str | None
) -> None:
    monkeypatch.setattr(
        mcp_server, "get_mcp_config", lambda: _FakeMCPConfig(accepted_roles, default_role)
    )


def test_resolve_role_defaults_to_configured_default_with_no_request_context(
    monkeypatch: pytest.MonkeyPatch,
):
    """Outside a live HTTP request (e.g. background task), get_http_headers() returns {}."""
    _patch_mcp_config(monkeypatch, accepted_roles=frozenset({"public", "drh"}), default_role="public")
    assert resolve_role() == "public"


def test_resolve_role_reads_an_accepted_header_value(monkeypatch: pytest.MonkeyPatch):
    _patch_mcp_config(monkeypatch, accepted_roles=frozenset({"public", "drh"}), default_role="public")
    monkeypatch.setattr(
        mcp_server, "get_http_headers", lambda: {CLICKHOUSE_ROLE_HEADER.lower(): "drh"}
    )
    assert resolve_role() == "drh"


def test_resolve_role_falls_back_to_default_on_unaccepted_value(monkeypatch: pytest.MonkeyPatch):
    """Fail closed: a role value outside CLICKHOUSE_MCP_ACCEPTED_ROLES never gets activated."""
    _patch_mcp_config(monkeypatch, accepted_roles=frozenset({"public", "drh"}), default_role="public")
    monkeypatch.setattr(
        mcp_server, "get_http_headers", lambda: {CLICKHOUSE_ROLE_HEADER.lower(): "admin"}
    )
    assert resolve_role() == "public"


def test_resolve_role_falls_back_to_default_when_header_absent(monkeypatch: pytest.MonkeyPatch):
    _patch_mcp_config(monkeypatch, accepted_roles=frozenset({"public", "drh"}), default_role="public")
    monkeypatch.setattr(mcp_server, "get_http_headers", lambda: {})
    assert resolve_role() == "public"


def test_resolve_role_returns_none_when_nothing_is_configured(monkeypatch: pytest.MonkeyPatch):
    """Unconfigured deployments (no env vars set) get role=None — unchanged ClickHouse behavior."""
    _patch_mcp_config(monkeypatch, accepted_roles=frozenset(), default_role=None)
    monkeypatch.setattr(mcp_server, "get_http_headers", lambda: {})
    assert resolve_role() is None
