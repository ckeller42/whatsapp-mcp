"""JID whitelist: an access-control layer for the WhatsApp MCP server.

The bridge stores *every* chat in the local database. This module restricts
which chats the MCP tools may read from or send to, based on an allow-list of
JIDs in a JSON file (``whitelist.json`` by default, overridable with the
``WHATSAPP_WHITELIST_PATH`` environment variable)::

    {"allowed_jids": ["491701234567@s.whatsapp.net", "12036...@g.us"]}

Security stance: **fail closed**. A missing, empty, or malformed whitelist
grants access to nothing. Enforcement lives at the SQL layer (``sql_filter``)
for reads and at ``is_allowed`` for sends, so there is a single choke point.
"""
import json
import os.path
from typing import List, Optional, Tuple

_ENV_PATH = "WHATSAPP_WHITELIST_PATH"
_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whitelist.json")


def _path() -> str:
    return os.environ.get(_ENV_PATH, _DEFAULT_PATH)


def is_active() -> bool:
    """Is the whitelist opted into?

    True if the operator set ``WHATSAPP_WHITELIST_PATH`` or created the default
    ``whitelist.json``. When inactive, access is unrestricted (backward
    compatible). Once active, enforcement applies and fails closed on error.
    """
    return _ENV_PATH in os.environ or os.path.exists(_DEFAULT_PATH)


def normalize_jid(recipient: Optional[str]) -> str:
    """Normalize a phone number or JID to a canonical bare JID (lowercased).

    - Bare phone numbers become ``<digits>@s.whatsapp.net``.
    - Existing JIDs keep their server; any device/agent suffix (``user:12@``)
      is stripped so comparisons are stable.
    - Empty / ``None`` input returns ``""`` (never matches a whitelist entry).
    """
    if not recipient:
        return ""
    r = recipient.strip().lower()
    if "@" in r:
        user, server = r.split("@", 1)
        user = user.split(":", 1)[0]
        server = server.split(":", 1)[0]
        return f"{user}@{server}"
    digits = "".join(ch for ch in r if ch.isdigit())
    return f"{digits}@s.whatsapp.net" if digits else ""


def load_whitelist() -> frozenset:
    """Load the set of allowed (normalized) JIDs. Fail closed on any error.

    Read fresh each call so edits to ``whitelist.json`` take effect on the next
    request without restarting; the file is tiny so the cost is negligible.
    """
    try:
        with open(_path()) as f:
            data = json.load(f)
        jids = data.get("allowed_jids", [])
        return frozenset(normalize_jid(j) for j in jids if j)
    except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError, TypeError):
        return frozenset()


def is_allowed(recipient: Optional[str]) -> bool:
    """True if the recipient may be contacted.

    Unrestricted when no whitelist is configured; otherwise only whitelisted
    JIDs pass, and a configured-but-empty/broken whitelist allows nothing.
    """
    if not is_active():
        return True
    wl = load_whitelist()
    if not wl:
        return False
    return normalize_jid(recipient) in wl


def sql_filter(column: str) -> Tuple[str, List[str]]:
    """Return a ``(clause, params)`` restricting ``column`` to whitelisted JIDs.

    Intended to be AND-ed into a WHERE clause. Comparison is case-insensitive
    to match the normalized whitelist. Unrestricted (``"1=1"``) when no
    whitelist is configured; fail closed (``"1=0"``, matches no rows) when a
    whitelist is configured but empty or broken.
    """
    if not is_active():
        return "1=1", []
    wl = list(load_whitelist())
    if not wl:
        return "1=0", []
    placeholders = ",".join("?" for _ in wl)
    return f"LOWER({column}) IN ({placeholders})", wl
