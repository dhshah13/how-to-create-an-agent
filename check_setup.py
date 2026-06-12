"""Pre-flight check. Run this the morning of the talk (and right before it).

  python3 check_setup.py
"""

import sys
import time

from config import MODEL, PROJECT_ID, REGION


def fail(msg, fix):
    print(f"  FAIL  {msg}")
    print(f"        fix: {fix}")
    sys.exit(1)


print(f"model:   {MODEL}")
print(f"project: {PROJECT_ID}")
print(f"region:  {REGION}")
print()

if not PROJECT_ID:
    fail("no GCP project configured",
         "export ANTHROPIC_VERTEX_PROJECT_ID=<your-project-id>")

try:
    import google.auth
    creds, _ = google.auth.default()
    print("  ok    found Google application-default credentials")
except Exception:
    fail("no Google credentials",
         "brew install google-cloud-sdk && gcloud auth application-default login")

import anthropic
from anthropic import AnthropicVertex

client = AnthropicVertex(project_id=PROJECT_ID, region=REGION)
t0 = time.time()
try:
    r = client.messages.create(
        model=MODEL, max_tokens=32,
        messages=[{"role": "user", "content": "Say 'ready'."}],
    )
except anthropic.AuthenticationError:
    fail("credentials rejected", "gcloud auth application-default login")
except anthropic.PermissionDeniedError:
    fail(f"project can't use {MODEL}",
         "enable the model in Vertex AI Model Garden and check you have roles/aiplatform.user")
except anthropic.NotFoundError:
    fail(f"{MODEL} not found in region '{REGION}'",
         "try CLOUD_ML_REGION=global, or DEMO_MODEL=claude-opus-4-6 / claude-sonnet-4-6")
except anthropic.APIConnectionError:
    fail("network error reaching Vertex", "check wifi/VPN; rehearse with DEMO_MOCK=1 if offline")

text = "".join(b.text for b in r.content if b.type == "text")
print(f"  ok    live call succeeded in {time.time() - t0:.1f}s -> {text.strip()!r}")
print()
print("all good. you're ready for Monday.")
