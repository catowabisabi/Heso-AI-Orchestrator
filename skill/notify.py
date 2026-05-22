#!/usr/bin/env python3
import os, sys, json, urllib.request
from datetime import datetime
import urllib.parse

BOT_TOKEN = os.environ.get("HESO_TG_TOKEN", "YOUR_BOT_TOKEN")
CHAT_ID  = os.environ.get("HESO_TG_CHAT_ID", "YOUR_CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def format_report(project, done_id, done_title, dispatch_id, dispatch_title,
                  todo_pending, todo_new, commit_hash):
    lines = [
        f"🍼 <b>{project}</b> · {datetime.now().strftime('%H:%M')}",
        f"✅ Done: #{done_id} {done_title}" if done_id else "✅ Done: —",
        f"🔧 Dispatched: #{dispatch_id} {dispatch_title}" if dispatch_id else "🔧 Dispatched: —",
        f"📋 TODO: {todo_pending} pending · {todo_new} new",
        f"📦 Commit: {commit_hash} → pushed" if commit_hash else "📦 Commit: none",
    ]
    return "\n".join(lines)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "send":
        project        = sys.argv[2]
        done_id        = sys.argv[3] if len(sys.argv) > 3 else ""
        done_title     = sys.argv[4] if len(sys.argv) > 4 else ""
        dispatch_id    = sys.argv[5] if len(sys.argv) > 5 else ""
        dispatch_title = sys.argv[6] if len(sys.argv) > 6 else ""
        pending        = sys.argv[7] if len(sys.argv) > 7 else "0"
        new_count      = sys.argv[8] if len(sys.argv) > 8 else "0"
        commit         = sys.argv[9] if len(sys.argv) > 9 else ""

        text = format_report(project, done_id, done_title, dispatch_id, dispatch_title,
                          pending, new_count, commit)
        send_message(text)

    elif cmd == "test":
        send_message("🍼 HESO test message · OK")

    else:
        print("usage: notify.py send <project> <done_id> <done_title> <dispatch_id> <dispatch_title> <pending> <new> <commit>")
        print("       notify.py test")