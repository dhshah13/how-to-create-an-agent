"""Shared client setup for all demo stages.

Reads:
  ANTHROPIC_VERTEX_PROJECT_ID  (or GOOGLE_CLOUD_PROJECT)  - your GCP project id
  CLOUD_ML_REGION              (or VERTEX_LOCATION)        - default: global
  DEMO_MODEL                                               - default: claude-opus-4-8
  DEMO_MOCK=1                                              - offline rehearsal mode, no API calls
"""

import os


def _load_demo_env():
    """Agent-driven shells (e.g. opencode's bash tool) may not inherit your
    exports. Fall back to a .demo-env file next to this script: KEY=VALUE lines.
    Real env vars always win."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".demo-env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_demo_env()

MODEL = os.environ.get("DEMO_MODEL", "claude-opus-4-6")
PROJECT_ID = os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
REGION = os.environ.get("CLOUD_ML_REGION") or os.environ.get("VERTEX_LOCATION") or "global"


def get_client():
    if os.environ.get("DEMO_MOCK") == "1":
        from mock_client import MockClient
        return MockClient()

    if not PROJECT_ID:
        raise SystemExit(
            "Set ANTHROPIC_VERTEX_PROJECT_ID to your GCP project id "
            "(and run `gcloud auth application-default login`). "
            "Or rehearse offline with DEMO_MOCK=1."
        )

    from anthropic import AnthropicVertex

    # Inside a sandbox with no gcloud install, inject a short-lived token instead:
    #   export ANTHROPIC_VERTEX_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
    # (valid ~1h - generate right before the talk)
    if token := os.environ.get("ANTHROPIC_VERTEX_ACCESS_TOKEN"):
        return AnthropicVertex(project_id=PROJECT_ID, region=REGION, access_token=token)

    return AnthropicVertex(project_id=PROJECT_ID, region=REGION)
