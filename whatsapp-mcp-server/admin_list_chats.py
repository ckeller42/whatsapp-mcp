"""Admin helper: list every chat in the local WhatsApp database with its JID.

This DELIBERATELY bypasses the whitelist so you can discover the JIDs to put
*into* whitelist.json. Run it once, interactively, to build your allow-list:

    uv run python admin_list_chats.py

Then copy the JIDs you want into whitelist.json (see whitelist.example.json).
Because it ignores the whitelist, it is not exposed as an MCP tool and should
only be run by you at a terminal.
"""
import sqlite3

from whatsapp import MESSAGES_DB_PATH


def main() -> None:
    conn = sqlite3.connect(MESSAGES_DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT jid, COALESCE(name, ''), COALESCE(last_message_time, '')
            FROM chats
            ORDER BY last_message_time DESC
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No chats found. Is the bridge running and synced?")
        return

    print(f"{'JID':45}  {'NAME':30}  LAST ACTIVE")
    print("-" * 90)
    for jid, name, last in rows:
        kind = "group" if jid.endswith("@g.us") else "dm"
        print(f"{jid:45}  {name[:30]:30}  {last}  ({kind})")
    print(f"\n{len(rows)} chats. Copy the JIDs you want into whitelist.json.")


if __name__ == "__main__":
    main()
