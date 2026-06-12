#!/bin/bash
# Security camera: live network decisions from the sandbox, one line per event.
# Run alongside cockpit.command - every tool call's egress shows up here,
# ALLOWED (with the policy that matched) or DENIED (with the reason).
# Double-click in Finder, or run:  open cagecam.command

cd "$(dirname "$0")" || exit 1

echo "[cagecam] streaming network decisions for sandbox 'agent-demo' (Ctrl+C to stop)"
echo "[cagecam] ALLOWED = matched a policy rule - DENIED = the cage said no"
echo

exec openshell logs agent-demo --tail 2>/dev/null | \
    grep --line-buffered -E "NET:OPEN|HTTP:GET|HTTP:POST"
