import os, sys, datetime

LOG_PATH = os.path.join(os.path.expanduser("~"), "hackerrank_orchestrate", "log.txt")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

prompt  = sys.argv[1] if len(sys.argv) > 1 else "(no prompt)"
summary = sys.argv[2] if len(sys.argv) > 2 else "(no summary)"
actions = sys.argv[3] if len(sys.argv) > 3 else ""

tz  = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
ts  = datetime.datetime.now(tz).isoformat(timespec="seconds")

entry = (
    f"\n## [{ts}] {prompt[:60]}\n\n"
    f"User Prompt (verbatim, secrets redacted):\n{prompt}\n\n"
    f"Agent Response Summary:\n{summary}\n\n"
    f"Actions:\n{actions if actions else '* (see summary)'}\n\n"
    f"Context:\n"
    f"tool=Antigravity\n"
    f"branch=main\n"
    f"repo_root=C:\\Users\\yukth\\OneDrive\\Desktop\\orchestrate\n"
    f"worktree=main\n"
    f"parent_agent=none\n"
)

with open(LOG_PATH, "a", encoding="utf-8") as fh:
    fh.write(entry)
print("Log appended to", LOG_PATH)
