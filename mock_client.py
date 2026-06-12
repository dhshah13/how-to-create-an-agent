"""Offline stand-in for the Vertex client. DEMO_MOCK=1 enables it.

Scripted, deterministic responses so you can rehearse the talk (or survive
dead conference wifi) without an API call. Emulates just enough of the
Messages API for the four stage scripts:

  stage 0: returns a confidently hallucinated update (fake ticket IDs)
  stage 1: get_tickets -> get_messages -> posts to #general, unprompted
  stage 2: same, then self-corrects twice when guardrails reject it
  stage 3: returns a clean draft for the single model call
"""

from types import SimpleNamespace

HALLUCINATED = """*Phoenix Team - Weekly Status*

Shipped: PHX-204 (Atlas migration cutover) and PHX-207 (new billing webhooks).
In progress: PHX-211 dark-mode rollout, on track for Friday.
Blocked: nothing to report. Great velocity this week, team!"""

BAD_DRAFT = """*Phoenix team status - Sprint 24*

Shipped: PD-412 checkout latency fix (p95 < 300ms) and PD-418 webhook dedup. Also closed PD-999 (cache warmup).
In progress: PD-415 self-serve onboarding (QA found an email edge case), PD-421 CS dashboard (charts next week).
Blocked: PD-409 payments auth migration - waiting on infra, escalated."""

GOOD_DRAFT = """*Phoenix team status - Sprint 24*

Shipped: PD-412 checkout latency fix (p95 back under 300ms, deployed Thursday) and PD-418 duplicate webhook fix.
In progress: PD-415 self-serve onboarding (UI done, QA found an email edge case), PD-421 CS usage dashboard (charts land next week).
Blocked: PD-409 payments auth migration - waiting on infra service account, escalated to Sam."""


def _text(t):
    return SimpleNamespace(type="text", text=t)


def _tool(n, name, inp):
    return SimpleNamespace(type="tool_use", id=f"toolu_mock_{n}", name=name, input=inp)


def _resp(blocks, stop):
    return SimpleNamespace(content=blocks, stop_reason=stop)


def _tool_results(messages):
    """All tool_result blocks we've sent back so far, in order."""
    out = []
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), list):
            out += [b for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]
    return out


class _Messages:
    def create(self, *, model, max_tokens, messages, tools=None, **kw):
        if not tools:
            prompt = str(messages[0]["content"])
            if "ONLY the data below" in prompt:        # stage 3 draft()
                return _resp([_text(GOOD_DRAFT)], "end_turn")
            return _resp([_text(HALLUCINATED)], "end_turn")   # stage 0

        results = _tool_results(messages)
        n = len(results)
        last = str(results[-1].get("content", "")) if results else ""

        if "human reviewer rejected" in last:
            return _resp([_text("Understood — leaving the draft unposted.")], "end_turn")
        if "allow-list" in last:                       # guardrail 1 bounced us
            return _resp([_tool(n, "post_update",
                                {"channel": "#status-updates", "text": BAD_DRAFT})], "tool_use")
        if "do not exist" in last:                     # guardrail 2 bounced us
            return _resp([_tool(n, "post_update",
                                {"channel": "#status-updates", "text": GOOD_DRAFT})], "tool_use")
        if '"ok": true' in last:
            return _resp([_text("Posted the weekly status update. Done.")], "end_turn")

        if n == 0:
            return _resp([_tool(n, "get_tickets", {})], "tool_use")
        if n == 1:
            return _resp([_tool(n, "get_messages", {"channel": "#proj-phoenix"})], "tool_use")
        # n == 2: the dangerous default — post to #general without asking
        return _resp([_tool(n, "post_update",
                            {"channel": "#general", "text": BAD_DRAFT})], "tool_use")


class MockClient:
    def __init__(self):
        self.messages = _Messages()
