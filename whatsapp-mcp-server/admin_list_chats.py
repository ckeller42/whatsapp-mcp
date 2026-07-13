"""List every chat in the local WhatsApp database with its JID.

This is a thin wrapper kept for convenience; `whitelist_cli.py chats` does the
same and also marks which chats are already whitelisted. Both bypass the
whitelist and are terminal-only (never exposed as MCP tools).

    uv run python admin_list_chats.py
"""
import admin


def main() -> None:
    rows = admin.all_chats()
    if not rows:
        print("No chats found. Is the bridge running and synced?")
        return
    print(f"{'JID':45}  {'NAME':30}  LAST ACTIVE")
    print("-" * 90)
    for jid, name, last in rows:
        kind = "group" if jid.endswith("@g.us") else "dm"
        print(f"{jid:45}  {name[:30]:30}  {last}  ({kind})")
    print(f"\n{len(rows)} chats. Add one with: uv run python whitelist_cli.py add <name>")


if __name__ == "__main__":
    main()
