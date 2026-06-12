"""Stage 3 - the same job, as a workflow.  (ADLC ~ design choice)

gather -> draft -> validate -> approve -> post

The model runs ONCE, inside draft(). Every other step is plain code.
Same output. Every step inspectable. Nothing picks its own path.
"""

import os
import re
import sys

from config import get_client, MODEL
from fake_tools import TICKETS, get_tickets, get_messages, post_update

client = get_client()


def gather() -> str:                       # plain code, no model
    return f"TICKETS:\n{get_tickets()}\n\nCHAT:\n{get_messages('#proj-phoenix')}"


def validate(text: str) -> str | None:     # plain code - same checks as stage 2
    if len(text) < 80:
        return "update is too short to be a real status update"
    mentioned = set(re.findall(r"PD-\d+", text))
    real = {t["id"] for t in TICKETS}
    if fake := mentioned - real:
        return f"references tickets that do not exist: {sorted(fake)}"
    if not mentioned:
        return "must reference at least one real ticket ID"
    return None


def draft(context: str, fix: str | None = None) -> str:    # the ONE model call
    prompt = (
        "Write this week's status update for the Phoenix team using ONLY the data below. "
        "Short sections: Shipped / In progress / Blocked. Reference ticket IDs.\n\n"
        + context
    )
    if fix:
        prompt += f"\n\nYour previous draft was rejected: {fix}. Fix that and only that."
    r = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(b.text for b in r.content if b.type == "text")


def approve(text: str) -> bool:            # plain code; agent-driven runs need DEMO_APPROVE=y
    print("\n----- DRAFT FOR APPROVAL " + "-" * 35)
    print(text)
    print("-" * 60)
    prompt = "Post this to #status-updates? [y/n] "
    if sys.stdin.isatty():
        return input(prompt).strip().lower() == "y"
    import select                       # peek, never block on agent-held stdin
    ready, _, _ = select.select([sys.stdin], [], [], 0.2)
    piped = sys.stdin.readline().strip() if ready else ""
    ans = piped or os.environ.get("DEMO_APPROVE", "n")
    print(f"{prompt}{ans}  [non-interactive]")
    return ans.lower() == "y"


# ----------------------------- the workflow: you can read the path
context = gather()
print("[1/4] gathered tickets + chat")

text = draft(context)
print("[2/4] drafted (model ran once)")

for attempt in range(2):                   # bounded retry, scripted by US
    err = validate(text)
    if err is None:
        break
    print(f"[3/4] validation failed: {err} -> redrafting")
    text = draft(context, fix=err)
else:
    sys.exit("draft failed validation twice; a human should write this one")
print("[3/4] validated")

if approve(text):
    post_update("#status-updates", text)
    print("[4/4] posted")
else:
    print("[4/4] not posted (human said no)")
