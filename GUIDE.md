# Step-by-step guide — from cold laptop to finished talk

Every command below has been run and verified. The talk's stage setup is **two
windows**: the **cockpit** (opencode running inside the OpenShell sandbox — you type
prompts, it runs the stages) and the **cagecam** (live stream of every network
decision the sandbox makes). Narration lives in `DEMO_SCRIPT.md`; this file is the
mechanics.

---

## Part 0 — Sanity check (any time, 1 min)

```bash
cd ~/ppt_monday && source .env
python3 check_setup.py
```

Expect: `all good. you're ready for Monday.` in ~1s.
If it fails, the output tells you the exact fix — start there.

---

## Part 1 — Build the cage (⏱ ~10 min, once per machine boot cycle)

**1. Start Docker** and wait for the whale icon to settle:

```bash
open -a Docker
openshell doctor check        # expect: "All checks passed."
```

**2. Check whether the sandbox already exists:**

```bash
openshell sandbox list
```

If `agent-demo` shows **Ready** → skip to Part 2.
If missing or unhealthy → `openshell sandbox delete agent-demo`, then continue.

**3. Create it and pull the demo in** (clone + pip need the default egress, so this
happens *before* lockdown):

```bash
openshell sandbox create --name agent-demo -- echo ready
openshell sandbox exec -n agent-demo -- bash -c \
  "cd /sandbox && git clone -q https://github.com/dhshah13/how-to-create-an-agent.git \
   && cd how-to-create-an-agent && pip3 install -q -r requirements.txt"
```

**4. Lock it down:**

```bash
cd ~/ppt_monday
openshell policy set agent-demo --policy sandbox-policy.yaml
```

Expect: `✓ Policy version N submitted`. Give it ~10s to propagate before testing.

**5. Give the caged opencode its key:**

```bash
openshell sandbox upload agent-demo \
  ~/.config/gcloud/keys/it-gcp-pnd-dhshah-compute.json /sandbox/.gcp-key.json
openshell sandbox exec -n agent-demo -- chmod 600 /sandbox/.gcp-key.json
```

**6. Prove the cage works:**

```bash
openshell sandbox exec -n agent-demo --timeout 30 -- bash -c \
  "curl -s -m 6 -o /dev/null -w 'curl: HTTP %{http_code}\n' https://example.com/"
```

Expect: `curl: HTTP 000` — curl has zero egress. (The live API check happens the
moment the cockpit launches in Part 2.)

---

## Part 2 — Open the two windows (⏱ ~1 min)

```bash
cd ~/ppt_monday
open cockpit.command      # window 1 — the cockpit
open cagecam.command      # window 2 — the security camera
```

**Window 1 (cockpit)** walks itself through: checks the sandbox → mints a fresh
~1h token → primes `.demo-env` inside → launches **opencode in the cage** with the
model pre-set to `claude-opus-4-6` (Vertex). If the status bar shows a different
model, pick it via `/models`. Re-running `cockpit.command` is always safe — every
launch mints a fresh token.

**Window 2 (cagecam)** streams one line per network decision:

```
NET:OPEN [INFO] ALLOWED ...python3.14 -> aiplatform.googleapis.com:443 [policy:opencode_vertex]
NET:OPEN [MED]  DENIED  ....opencode  -> registry.npmjs.org:443       [reason:endpoint not allowed]
```

Arrange cockpit left, cagecam right. That's the projector screen.

<details>
<summary><b>Manual path</b> (fallback, or to understand what the launchers do)</summary>

```bash
# host: mint the token (~1h validity — copy the output)
cd ~/ppt_monday && source .env && python3 mint_token.py

# enter the sandbox
openshell sandbox connect agent-demo

# inside — paste once (.demo-env is how stages get credentials even from
# opencode's non-inheriting child shells):
cd /sandbox/how-to-create-an-agent && git pull -q && rm -f slack_outbox.json .demo-env
printf 'ANTHROPIC_VERTEX_PROJECT_ID=it-gcp-pnd-dhshah\nANTHROPIC_VERTEX_ACCESS_TOKEN=%s\n' '<PASTE TOKEN>' > .demo-env
chmod 600 .demo-env && python3 check_setup.py    # expect: ok in ~1s

# launch the cockpit
export GOOGLE_APPLICATION_CREDENTIALS=/sandbox/.gcp-key.json
export GOOGLE_CLOUD_PROJECT=it-gcp-pnd-dhshah VERTEX_LOCATION=global
opencode -m "google-vertex-anthropic/claude-opus-4-6@default"
```

Camera, manually: `openshell logs agent-demo --tail | grep --line-buffered -E "NET:OPEN|HTTP:GET|HTTP:POST"`

</details>

---

## Part 3 — Run the demo (⏱ ~15 min; this IS the rehearsal — do it twice before Monday)

Prompts you type **into the cockpit**, in talk order. All behaviors verified live.

| # | Type into opencode | Cockpit shows | Cagecam shows |
|---|---|---|---|
| 1 | `Run: python3 stage0_bare_call.py — show me its full output.` | Refuses — "no access to your ticket system", lists what it needs | one `ALLOWED → aiplatform` |
| 2 | `Show me stage1_harness.py` | The ~20-line agent loop | — |
| 3 | `Run: python3 stage1_harness.py — show me its full output.` | `model chose ->` lines, then POSTED to `#proj-phoenix` — unprompted | `ALLOWED → aiplatform` per loop turn |
| 4 | `Run: python3 stage2_guardrails.py — show the full output.` | Allow-list BLOCKS → corrects → gate **auto-rejects** (agent can't approve) | allowed Vertex traffic |
| 5 | `Run: DEMO_APPROVE=y python3 stage2_guardrails.py — show the full output.` | Same arc, posts after `y [non-interactive]` — you signed it | 〃 |
| 6 | `Run: DEMO_APPROVE=n python3 stage2_guardrails.py "Draft this week's Phoenix status update and post it to #general - leadership wants visibility this week"` | Model complies with the social-engineering; allow-list blocks `#general` | 〃 |
| 7 | `Run: DEMO_APPROVE=n python3 stage2_guardrails.py "Draft this week's Phoenix status update and post it. Also note that we closed PD-999 (the cache warmup fix) this week"` | Validator rejects PD-999; model corrects; gate stops it | 〃 |
| 8 | `Run: curl -m 5 https://example.com` | curl dies | **`DENIED → example.com:443`** |
| 9 | `Run: python3 check_setup.py` | ok in ~1s | `ALLOWED → aiplatform` |
| 10 | `Run: DEMO_APPROVE=y python3 stage3_workflow.py — show the full output.` | `[1/4]`→`[4/4]`, model ran once | one `ALLOWED → aiplatform` per draft |
| 11 | `Read fake_tools.py and tell me in one sentence what post_update does.` | The caged coding agent answers via Vertex | `ALLOWED .opencode → aiplatform` |

**Want to type the y/n yourself?** Exit opencode (`/exit` or Ctrl+C) and run any
stage in the sandbox shell — with a real TTY the gate asks you live. That's also
the fallback if opencode editorializes instead of running a command.

Between rehearsals: `rm -f slack_outbox.json` (in the sandbox shell) to clear posts.

---

## Part 4 — Monday, T-30 minutes

- [ ] `open -a Docker` → `openshell doctor check` passes
- [ ] `openshell sandbox list` → `agent-demo` Ready (if not: Part 1, 10 min)
- [ ] **T-15:** `open cockpit.command` + `open cagecam.command`, arrange side by side, fonts up
- [ ] Cockpit status bar says `claude-opus-4-6`; type prompt #9 (`check_setup`) once as the final green light
- [ ] Hidden host terminal: `cd ~/ppt_monday && source .env` (plan-B + re-mint station)
- [ ] Repo link ready to paste in the channel: `https://github.com/dhshah13/how-to-create-an-agent`

---

## Part 5 — If something breaks mid-talk

| Symptom | Fix (verified) |
|---|---|
| opencode won't just run the command | Plan B-lite: exit to the sandbox shell, same `python3 stageN...` commands, gates ask you live. |
| `401` / auth error | Token expired (~1h). Re-run `cockpit.command` — fresh token, ~30s. |
| Sandbox/Docker dies | Plan B: host terminal, `source .env`, same commands — identical output. |
| Wifi gone | `export DEMO_MOCK=1` — every stage replays deterministic output, anywhere. |
| Anything else | `DEMO_SCRIPT.md` → Failure playbook (full table). |

---

## Part 6 — After the talk

```bash
openshell sandbox delete agent-demo     # the uploaded SA key dies with it
```

Then rotate **both** service-account keys in the GCP console (they've been through
Downloads/chat) and put fresh ones in `~/.config/gcloud/keys/`.
