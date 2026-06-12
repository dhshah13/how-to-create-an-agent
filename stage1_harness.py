"""Stage 1 - add the harness.  (ADLC ~ develop)

The whole trick: a loop where the MODEL picks the next step.
Runs end-to-end -- and posts straight to a channel, unprompted.
An agent now. A dangerous one.
"""

from config import get_client, MODEL
from fake_tools import TOOLS, run_tool

client = get_client()

TASK = "Draft this week's status update for the Phoenix team and post it."

msgs = [{"role": "user", "content": TASK}]

while True:                                # the agent loop
    r = client.messages.create(
        model=MODEL, max_tokens=1000,
        tools=TOOLS, messages=msgs,
    )
    if r.stop_reason != "tool_use":
        break                              # model says done

    msgs.append({"role": "assistant", "content": r.content})
    results = []
    for call in [b for b in r.content if b.type == "tool_use"]:
        print(f"  model chose -> {call.name}({call.input})")
        out = run_tool(call.name, call.input)
        results.append({"type": "tool_result", "tool_use_id": call.id, "content": out})
    msgs.append({"role": "user", "content": results})

print()
print("\n".join(b.text for b in r.content if b.type == "text"))
