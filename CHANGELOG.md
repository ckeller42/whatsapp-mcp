# Changelog

All notable changes to this fork are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This is a fork of [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp).
Changes below are relative to upstream `main` (`7d6a06d`).

## [0.1.0] — unreleased

### Added

- **Optional JID whitelist** restricting which chats the MCP server can read or
  send to. Enforced at the SQL layer for reads and before any network call for
  sends, and **fails closed**: a missing, unreadable, or malformed whitelist
  file exposes nothing rather than everything.
- `whitelist_cli.py` to list, add, and remove whitelisted chats.
- **Phone-number pairing** for the bridge (`WHATSAPP_PAIR_PHONE`) plus raw QR
  output, so the bridge can be linked on a headless host.
- Configurable message database location via `WHATSAPP_MESSAGES_DB`.
- Documentation for macOS `launchd` service setup for the bridge.
- Test suite: 64 tests covering whitelist enforcement, normalization,
  fail-closed behavior, the CLI, and the fixes below.

### Fixed

- **Bridge "client outdated (405)"** — updated `whatsmeow` to a working revision.
- **`list_chats` / `get_chat` returned nothing when `include_last_message=False`.**
  Both selected `messages.content` / `.sender` / `.is_from_me` unconditionally
  but only joined the `messages` table when the flag was true, so sqlite raised
  `no such column: messages.content` and the broad `except sqlite3.Error`
  swallowed it into an empty result. Upstream defect, present since `76d332b`.
- **Diagnostics no longer corrupt the MCP protocol.** `main.py` serves over
  `mcp.run(transport='stdio')`, so stdout carries the JSON-RPC frames; 17 bare
  `print()` calls in `whatsapp.py` wrote plain text into that channel. All now
  go to stderr. Upstream defect.
- Whitelist filtering now matches on the normalized JID rather than raw input,
  closing a bypass via unnormalized forms.

### Security

- The whitelist is enforced in the SQL `WHERE` clause on every read path, so a
  non-whitelisted chat cannot surface even if a caller passes its JID directly.
- The real `whitelist.json` is git-ignored and never committed.

[0.1.0]: https://github.com/ckeller42/whatsapp-mcp/compare/v0.0.1...HEAD
