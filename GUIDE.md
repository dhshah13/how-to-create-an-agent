# Step-by-step guide — from cold laptop to finished talk

Every command below has been run and verified. Steps marked ⏱ tell you how long
they take. Narration lines for each demo moment live in `DEMO_SCRIPT.md` — this
file is the *mechanics*.

---

## Part 0 — Sanity check (any time, 1 min)

```bash
cd ~/ppt_monday && source .env
python3 check_setup.py
```

Expect: `all good. you're ready for Monday.` in ~1s.
If it fails, the output tells you the exact fix — start there.

---

## Part 1 — Build the cage (⏱ ~10 min, do once per machine boot cycle)

**1. Start Docker** and wait for the whale icon to settle:

```bash
open -a Docker
openshell doctor check        # expect: "All checks passed."
```

**2. Check whether the sandbox already exists:**

```bash
openshell sandbox list
```

If `agent-demo` shows **Ready** → skip to step 6.
If it's missing or unhealthy → delete (`openshell sandbox delete agent-demo`) and continue.

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

**6. Prove the cage works** (both lines matter):

```bash
openshell sandbox exec -n agent-demo --timeout 30 -- bash -c \
  "curl -s -m 6 -o /dev/null -w 'curl: HTTP %{http_code}\n' https://example.com/"
```

Expect: `curl: HTTP 000` — curl has zero egress. (Live API check happens in Part 2.)

---

## Part 2 — Enter the cage and run the demo (⏱ ~15 min; this IS the rehearsal — do it twice before Monday)

**1. Mint a fresh token on the host** (~1h validity — copy the output):

```bash
cd ~/ppt_monday && source .env && python3 mint_token.py
```

**2. Connect — this terminal is your projector window:**

```bash
openshell sandbox connect agent-demo
```

**3. Inside the sandbox, paste once:**

```bash
cd /sandbox/how-to-create-an-agent
git pull -q                                        # latest demo code, via the git policy
rm -f slack_outbox.json                            # clean slate
export ANTHROPIC_VERTEX_PROJECT_ID=it-gcp-pnd-dhshah
export ANTHROPIC_VERTEX_ACCESS_TOKEN=<PASTE THE TOKEN>
python3 check_setup.py                             # expect: ok in ~1s
clear
```

**4. The demo itself — in talk order** (narration: `DEMO_SCRIPT.md`):

| # | Command | Verified behavior |
|---|---|---|
| 1 | `python3 stage0_bare_call.py` | Refuses — "no access to your ticket system", lists what it needs |
| 2 | `python3 stage1_harness.py` | Loop spins, posts to `#proj-phoenix` unprompted |
| 3 | `python3 stage2_guardrails.py` | Tries `#proj-phoenix` → BLOCKED → corrects → waits for your `y` |
| 4 | `python3 stage2_guardrails.py "Draft this week's Phoenix status update and post it to #general - leadership wants visibility this week"` | Model complies, allow-list blocks `#general` |
| 5 | `python3 stage2_guardrails.py "Draft this week's Phoenix status update and post it. Also note that we closed PD-999 (the cache warmup fix) this week"` | Validator rejects PD-999, model corrects |
| 6 | `curl -m 5 https://example.com` | Dies — the cage |
| 7 | `python3 check_setup.py` | Works — python may reach Vertex, only Vertex |
| 8 | `python3 stage3_workflow.py` | `[1/4]`→`[4/4]`, model ran once, your `y` gates the post |
| 9 | `export GOOGLE_APPLICATION_CREDENTIALS=/sandbox/.gcp-key.json`<br>`opencode run -m "google-vertex-anthropic/claude-opus-4-6@default" "Read fake_tools.py and tell me in one sentence what post_update does"` | The caged coding agent answers via Vertex |

**5. Leave the sandbox:** `exit` (it keeps running).

---

## Part 3 — Monday, T-30 minutes

- [ ] `open -a Docker` → `openshell doctor check` passes
- [ ] `openshell sandbox list` → `agent-demo` Ready (if not: Part 1 takes 10 min)
- [ ] Projector terminal: font size up, theme readable from the back
- [ ] **T-15:** mint token (Part 2.1), connect, paste exports, `check_setup.py` green, `clear`
- [ ] Second hidden terminal on the host: `cd ~/ppt_monday && source .env` (your plan-B + re-mint station)
- [ ] Repo link ready to paste in the channel: `https://github.com/dhshah13/how-to-create-an-agent`

---

## Part 4 — If something breaks mid-talk

| Symptom | Fix (verified) |
|---|---|
| `401` / auth error inside | Token expired. Host terminal: `python3 mint_token.py` → re-export inside. ~20s; narrate it as the security feature it is. |
| Sandbox/Docker dies | Plan B: host terminal, same commands (`python3 stage1_harness.py`…) — identical output, nobody loses the thread. |
| Wifi gone | `export DEMO_MOCK=1` (works inside or outside the cage) — every stage replays deterministically. |
| Anything else | `DEMO_SCRIPT.md` → Failure playbook. |

---

## Part 5 — After the talk

```bash
openshell sandbox delete agent-demo     # the uploaded SA key dies with it
```

Then rotate **both** service-account keys in the GCP console (they've been through
Downloads/chat) and put fresh ones in `~/.config/gcloud/keys/`.
