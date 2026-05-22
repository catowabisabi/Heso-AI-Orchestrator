#!/usr/bin/env python3
import sqlite3, os, sys, json

BASE = os.path.expanduser("~/.hermes/autoloop")
DB   = os.path.join(BASE, "progress.db")

POOL_MAX   = 1000
SEED_KW    = 20
PICK_SRC   = 5
GEN_PER_KW = 10
USE_IN_PROMPT = 3

INIT_KEYWORDS = [
    "information design", "happiness", "human machine interaction",
    "inclusive design", "trust", "friction", "memory", "ritual",
    "serendipity", "calm technology", "feedback loop", "affordance",
    "delight", "accessibility", "flow state", "ambient awareness",
    "constraint", "playfulness", "legibility", "resilience",
]

def conn():
    os.makedirs(BASE, exist_ok=True)
    return sqlite3.connect(DB)

def init_pool():
    c = conn(); cur = c.cursor()
    for w in INIT_KEYWORDS:
        cur.execute("INSERT OR IGNORE INTO keyword_pool(word) VALUES (?)", (w.lower(),))
    c.commit(); c.close()
    print(f"pool seeded: {len(INIT_KEYWORDS)} keywords")

def pool_count():
    c = conn(); n = c.execute("SELECT COUNT(*) FROM keyword_pool").fetchone()[0]; c.close()
    return n

def pick_sources():
    c = conn()
    rows = c.execute("SELECT word FROM keyword_pool ORDER BY RANDOM() LIMIT ?",
                     (PICK_SRC,)).fetchall()
    c.close()
    return [r[0] for r in rows]

def add_words(words):
    c = conn(); cur = c.cursor()
    for w in words:
        w = w.strip().lower()
        if w:
            cur.execute("INSERT OR IGNORE INTO keyword_pool(word) VALUES (?)", (w,))
    c.commit()
    n = cur.execute("SELECT COUNT(*) FROM keyword_pool").fetchone()[0]
    if n > POOL_MAX:
        over = n - POOL_MAX
        ids = cur.execute("SELECT id FROM keyword_pool ORDER BY RANDOM() LIMIT ?",
                          (over,)).fetchall()
        cur.executemany("DELETE FROM keyword_pool WHERE id=?", ids)
        c.commit()
    c.close()
    print(f"pool now: {min(n, POOL_MAX)}")

def pick_for_prompt():
    c = conn()
    rows = c.execute("SELECT word FROM keyword_pool ORDER BY RANDOM() LIMIT ?",
                     (USE_IN_PROMPT,)).fetchall()
    c.close()
    return [r[0] for r in rows]

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "init":
        init_pool()
    elif cmd == "count":
        print(pool_count())
    elif cmd == "sources":
        print(json.dumps(pick_sources(), ensure_ascii=False))
    elif cmd == "add":
        add_words(sys.argv[2].split(","))
    elif cmd == "prompt3":
        print(json.dumps(pick_for_prompt(), ensure_ascii=False))
    else:
        print("usage: init | count | sources | add <csv> | prompt3")