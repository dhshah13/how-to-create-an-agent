#!/bin/bash
# One-click cockpit: opens opencode inside the OpenShell sandbox, ready to demo.
# Double-click in Finder, or run:  open cockpit.command

cd "$(dirname "$0")" || exit 1
source .env 2>/dev/null

echo "[cockpit] checking sandbox..."
if ! openshell sandbox list 2>/dev/null | grep -q "agent-demo.*Ready"; then
    echo "[cockpit] sandbox 'agent-demo' is not Ready - run GUIDE.md Part 1 first."
    exec bash
fi

echo "[cockpit] minting fresh Vertex token (~1h)..."
TOKEN=$(python3 mint_token.py) || { echo "[cockpit] token mint failed - check .env / keys"; exec bash; }

echo "[cockpit] priming .demo-env in the sandbox..."
printf 'ANTHROPIC_VERTEX_PROJECT_ID=%s\nANTHROPIC_VERTEX_ACCESS_TOKEN=%s\n' \
    "it-gcp-pnd-dhshah" "$TOKEN" | \
    openshell sandbox exec -n agent-demo --timeout 60 -- bash -c \
    "cat > /sandbox/how-to-create-an-agent/.demo-env && chmod 600 /sandbox/how-to-create-an-agent/.demo-env"

echo "[cockpit] launching opencode in the cage (exit with /exit or Ctrl+C)..."
exec openshell sandbox exec -n agent-demo --tty \
    --workdir /sandbox/how-to-create-an-agent -- \
    env HOME=/sandbox TERM=xterm-256color \
        GOOGLE_APPLICATION_CREDENTIALS=/sandbox/.gcp-key.json \
        GOOGLE_CLOUD_PROJECT=it-gcp-pnd-dhshah \
        VERTEX_LOCATION=global \
        /usr/bin/opencode -m "google-vertex-anthropic/claude-opus-4-6@default"
