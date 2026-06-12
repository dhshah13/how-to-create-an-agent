"""Stage 0 - a bare LLM call.  (ADLC ~ experiment)

No tools. No data. Older models bluffed here (invented ticket IDs);
2026 models refuse and ask for the data instead. Either way it's the
same lesson: zero live data, zero actions. A chatbot. Not an agent.

Bonus: read its reply closely - it lists exactly what it needs.
Stage 1 gives it exactly that.
"""

from config import get_client, MODEL

client = get_client()

resp = client.messages.create(
    model=MODEL,
    max_tokens=500,
    messages=[{"role": "user",
               "content": "Draft this week's status update for the Phoenix team. "
                          "Include ticket IDs and what shipped."}],
)

print(resp.content[0].text)
# that's it. that's the whole thing.
