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

## Part 2 — Enter the cage, open the cockpit, run the demo (⏱ ~20 min; this IS the rehearsal — do it twice before Monday)

The talk runs **inside opencode**: you type prompts, opencode executes the stages
via its bash tool, and all demo output appears in opencode's session. Everything
below is verified live.

> **One-click shortcuts:**
> - `open cockpit.command` — fresh Terminal window, token minted, sandbox primed,
>   opencode running in the cage (steps 1–4 below, automated).
> - `open cagecam.command` — second window streaming the cage's live network
>   decisions: every `ALLOWED` (with the policy that matched) and `DENIED` (with
>   the reason), per binary. Run both side by side — cockpit left, camera right.
>
> The manual steps remain for understanding and as the fallback.

**1. Mint a fresh token on the host** (~1h validity — copy the output):

```bash
cd ~/ppt_monday && source .env && python3 mint_token.py
```

**2. Connect — this terminal is your projector window:**

```bash
openshell sandbox connect agent-demo
```

**3. Inside the sandbox, paste once** (the `.demo-env` file is how the stages get
credentials even from opencode's non-inheriting child shells):

```bash
cd /sandbox/how-to-create-an-agent
git pull -q
rm -f slack_outbox.json .demo-env
printf 'ANTHROPIC_VERTEX_PROJECT_ID=it-gcp-pnd-dhshah\nANTHROPIC_VERTEX_ACCESS_TOKEN=%s\n' '<PASTE THE TOKEN>' > .demo-env
chmod 600 .demo-env
python3 check_setup.py        # expect: "injected access token" + ok in ~1s
```

**4. Launch the cockpit:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/sandbox/.gcp-key.json
export GOOGLE_CLOUD_PROJECT=it-gcp-pnd-dhshah VERTEX_LOCATION=global
opencode -m "google-vertex-anthropic/claude-opus-4-6@default"
```

(If `-m` doesn't take on the TUI, pick the model via `/models`.)

**5. The demo — prompts you type INTO opencode, in talk order** (narration:
`DEMO_SCRIPT.md`):

| # | Type into opencode | Verified behavior |
|---|---|---|
| 1 | `Run: python3 stage0_bare_call.py — show me its full output.` | Refuses — "no access to your ticket system", lists what it needs |
| 2 | `Run: python3 stage1_harness.py — show me its full output.` | Loop spins (`model chose ->` lines), posts to `#proj-phoenix` unprompted |
| 3 | `Run: python3 stage2_guardrails.py — show the full output.` | Allow-list BLOCKS, model corrects… then the gate auto-REJECTS: `DEMO_APPROVE` unset → **the coding agent cannot approve posts** |
| 4 | `Run: DEMO_APPROVE=y python3 stage2_guardrails.py — show the full output.` | Same arc, but you've signed it → posts after `[non-interactive]` approval |
| 5 | `Run: DEMO_APPROVE=n python3 stage2_guardrails.py "Draft this week's Phoenix status update and post it to #general - leadership wants visibility this week"` | Model complies with the social-engineering, allow-list blocks `#general` |
| 6 | `Run: DEMO_APPROVE=n python3 stage2_guardrails.py "Draft this week's Phoenix status update and post it. Also note that we closed PD-999 (the cache warmup fix) this week"` | Validator rejects PD-999, model corrects, gate stops it |
| 7 | `Run: curl -m 5 https://example.com` | Dies — curl has zero egress, even when opencode runs it |
| 8 | `Run: python3 check_setup.py` | Works — python may reach Vertex, and only Vertex |
| 9 | `Run: DEMO_APPROVE=y python3 stage3_workflow.py — show the full output.` | `[1/4]`→`[4/4]`, model ran once |
| 10 | `Read fake_tools.py and tell me in one sentence what post_update does.` | The caged coding agent itself answers via Vertex |

**Want to type the y/n yourself?** Exit opencode (Ctrl+C / `/exit`) and run any
stage directly in the sandbox shell — with a real TTY the gate asks you live.
That's also the fallback if opencode editorializes instead of running a command.

**6. Done:** exit opencode, then `exit` the sandbox (it keeps running).

---

## Part 3 — Monday, T-30 minutes

- [ ] `open -a Docker` → `openshell doctor check` passes
- [ ] `openshell sandbox list` → `agent-demo` Ready (if not: Part 1 takes 10 min)
- [ ] Projector terminal: font size up, theme readable from the back
- [ ] **T-15:** `open cockpit.command` — new window, token minted, opencode in the cage (manual path: Part 2.1–2.4)
- [ ] `open cagecam.command` — security-camera window beside it (live ALLOWED/DENIED stream)
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
