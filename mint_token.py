"""Mint a ~1-hour Vertex access token from your Google credentials (host side).

Works with either `gcloud auth application-default login` ADC or a
GOOGLE_APPLICATION_CREDENTIALS service-account key. No gcloud binary needed.

Usage:
  export ANTHROPIC_VERTEX_ACCESS_TOKEN=$(python3 mint_token.py)

Paste that token into the sandbox - it expires in ~1h and nothing
long-lived ever enters the box.
"""

import google.auth
from google.auth.transport.requests import Request

creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
creds.refresh(Request())
print(creds.token)
