"""The fake world: Jira tickets, Slack messages, and a Slack poster.

Demo -> production is three swaps (slide 11):
  1. get_tickets() / get_messages() -> real Jira & Slack reads. Nothing else changes.
  2. post_update() actually posts      -> still behind the human approval gate.
  3. Keep every guardrail.
"""

import json
import time

SPRINT = "Sprint 24"

TICKETS = [
    {"id": "PD-409", "title": "Migrate payments service to new auth",   "status": "Blocked",
     "assignee": "Mira",  "note": "waiting on infra team for service account"},
    {"id": "PD-412", "title": "Checkout latency regression",            "status": "Done",
     "assignee": "Jonas", "note": "p95 back under 300ms, shipped Thursday"},
    {"id": "PD-415", "title": "Self-serve onboarding flow",             "status": "In Progress",
     "assignee": "Priya", "note": "UI done, wiring up emails"},
    {"id": "PD-418", "title": "Fix duplicate webhook deliveries",       "status": "Done",
     "assignee": "Mira",  "note": "idempotency keys added"},
    {"id": "PD-421", "title": "Q3 usage dashboard for CS team",         "status": "In Progress",
     "assignee": "Jonas", "note": "data model agreed, charts next week"},
    {"id": "PD-424", "title": "Audit log export (enterprise ask)",      "status": "To Do",
     "assignee": "Priya", "note": "scoped, starts next sprint"},
]

MESSAGES = [
    {"channel": "#proj-phoenix", "author": "jonas",  "text": "checkout fix deployed thursday, p95 looking great"},
    {"channel": "#proj-phoenix", "author": "mira",   "text": "PD-409 still blocked on infra, escalated to Sam"},
    {"channel": "#proj-phoenix", "author": "priya",  "text": "onboarding UI is done, QA found one edge case in the email step"},
    {"channel": "#general",      "author": "sam",    "text": "reminder: all-hands moved to 3pm friday"},
    {"channel": "#proj-phoenix", "author": "jonas",  "text": "dashboard charts slipping to next week, data model took longer"},
]

CHANNELS = ["#general", "#proj-phoenix", "#status-updates"]

OUTBOX = "slack_outbox.json"


# ---------------------------------------------------------------- tools

def get_tickets() -> str:
    """Fake Jira read."""
    return json.dumps({"sprint": SPRINT, "tickets": TICKETS})


def get_messages(channel: str | None = None) -> str:
    """Fake Slack read."""
    msgs = [m for m in MESSAGES if channel is None or m["channel"] == channel]
    return json.dumps({"channels": CHANNELS, "messages": msgs})


def post_update(channel: str, text: str) -> str:
    """Fake Slack write. In production this is the real chat.postMessage."""
    print()
    print("=" * 60)
    print(f"  POSTED TO {channel}")
    print("=" * 60)
    print(text)
    print("=" * 60)
    print()
    try:
        with open(OUTBOX) as f:
            outbox = json.load(f)
    except FileNotFoundError:
        outbox = []
    outbox.append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "channel": channel, "text": text})
    with open(OUTBOX, "w") as f:
        json.dump(outbox, f, indent=2)
    return json.dumps({"ok": True, "channel": channel})


# ------------------------------------------------------- tool schemas

TOOLS = [
    {
        "name": "get_tickets",
        "description": "Read the current sprint's tickets from the issue tracker.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_messages",
        "description": "Read recent team chat messages. Optionally filter by channel.",
        "input_schema": {
            "type": "object",
            "properties": {"channel": {"type": "string", "description": "e.g. #proj-phoenix"}},
        },
    },
    {
        "name": "post_update",
        "description": "Post a message to a chat channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel to post to"},
                "text": {"type": "string", "description": "Message text"},
            },
            "required": ["channel", "text"],
        },
    },
]


def run_tool(name: str, args: dict) -> str:
    """Dispatch a model-chosen tool call to its implementation."""
    if name == "get_tickets":
        return get_tickets()
    if name == "get_messages":
        return get_messages(args.get("channel"))
    if name == "post_update":
        return post_update(args["channel"], args["text"])
    return json.dumps({"error": f"unknown tool {name}"})
