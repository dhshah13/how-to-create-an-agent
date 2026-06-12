"""Stage 0 - a bare LLM call.  (ADLC ~ experiment)

No tools. No data. Watch it invent ticket IDs that don't exist.
A chatbot. Not an agent.
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
