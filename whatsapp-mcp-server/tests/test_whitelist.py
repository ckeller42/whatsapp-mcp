"""Tests for the JID whitelist access-control layer.

The whitelist is a security boundary: it decides which WhatsApp chats the MCP
server may read from or send to. The most important property is that it
*fails closed* — any misconfiguration must deny access, never grant it.
"""
import json

import pytest

import whitelist


@pytest.fixture
def wl_file(tmp_path, monkeypatch):
    """Point the whitelist loader at a temp file; return a writer for it."""
    path = tmp_path / "whitelist.json"
    monkeypatch.setenv("WHATSAPP_WHITELIST_PATH", str(path))

    def write(jids):
        path.write_text(json.dumps({"allowed_jids": jids}))

    return write, path


# --- normalize_jid ---------------------------------------------------------

def test_normalize_bare_phone_becomes_individual_jid():
    assert whitelist.normalize_jid("491701234567") == "491701234567@s.whatsapp.net"


def test_normalize_phone_strips_plus_and_symbols():
    assert whitelist.normalize_jid("+49 170 1234567") == "491701234567@s.whatsapp.net"


def test_normalize_individual_jid_passthrough():
    assert whitelist.normalize_jid("491701234567@s.whatsapp.net") == "491701234567@s.whatsapp.net"


def test_normalize_group_jid_passthrough():
    assert whitelist.normalize_jid("120363012345678901@g.us") == "120363012345678901@g.us"


def test_normalize_strips_device_suffix():
    # WhatsApp appends a device/agent suffix to the user part: user:12@server
    assert whitelist.normalize_jid("491701234567:12@s.whatsapp.net") == "491701234567@s.whatsapp.net"


def test_normalize_empty_returns_empty():
    assert whitelist.normalize_jid("") == ""
    assert whitelist.normalize_jid(None) == ""


# --- is_allowed: fail closed ----------------------------------------------

def test_is_allowed_true_for_whitelisted_jid(wl_file):
    write, _ = wl_file
    write(["491701234567@s.whatsapp.net"])
    assert whitelist.is_allowed("491701234567@s.whatsapp.net") is True


def test_is_allowed_matches_phone_against_jid_whitelist(wl_file):
    write, _ = wl_file
    write(["491701234567@s.whatsapp.net"])
    # caller passes a bare phone number; must normalize and match
    assert whitelist.is_allowed("+49 170 1234567") is True


def test_is_allowed_false_for_non_whitelisted(wl_file):
    write, _ = wl_file
    write(["491701234567@s.whatsapp.net"])
    assert whitelist.is_allowed("999999999@s.whatsapp.net") is False


def test_is_allowed_false_when_whitelist_empty(wl_file):
    write, _ = wl_file
    write([])
    assert whitelist.is_allowed("491701234567@s.whatsapp.net") is False


def test_is_allowed_false_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("WHATSAPP_WHITELIST_PATH", str(tmp_path / "does-not-exist.json"))
    assert whitelist.is_allowed("491701234567@s.whatsapp.net") is False


def test_is_allowed_false_when_file_malformed(wl_file):
    _, path = wl_file
    path.write_text("{not valid json")
    assert whitelist.is_allowed("491701234567@s.whatsapp.net") is False


# --- opt-in: unrestricted only when NOTHING is configured -----------------

def test_unrestricted_when_no_whitelist_configured(tmp_path, monkeypatch):
    # No env var and no default file => backward-compatible open access.
    monkeypatch.delenv("WHATSAPP_WHITELIST_PATH", raising=False)
    monkeypatch.setattr(whitelist, "_DEFAULT_PATH", str(tmp_path / "absent.json"))
    assert whitelist.is_allowed("491701234567@s.whatsapp.net") is True
    assert whitelist.is_allowed("anyone@s.whatsapp.net") is True


def test_sql_filter_open_when_no_whitelist_configured(tmp_path, monkeypatch):
    monkeypatch.delenv("WHATSAPP_WHITELIST_PATH", raising=False)
    monkeypatch.setattr(whitelist, "_DEFAULT_PATH", str(tmp_path / "absent.json"))
    clause, params = whitelist.sql_filter("chats.jid")
    assert clause == "1=1"
    assert params == []


# --- sql_filter: fail closed ----------------------------------------------

def test_sql_filter_returns_in_clause_and_params(wl_file):
    write, _ = wl_file
    write(["491701234567@s.whatsapp.net", "120363012345678901@g.us"])
    clause, params = whitelist.sql_filter("chats.jid")
    assert "chats.jid" in clause
    assert clause.count("?") == 2
    assert set(params) == {"491701234567@s.whatsapp.net", "120363012345678901@g.us"}


def test_sql_filter_matches_nothing_when_empty(wl_file):
    write, _ = wl_file
    write([])
    clause, params = whitelist.sql_filter("chats.jid")
    assert clause == "1=0"
    assert params == []
