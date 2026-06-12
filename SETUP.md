# Set up your own agent (from this repo)

You watched the talk (or found this repo) and want the agent running on **your**
machine — and then to turn it into **your own** agent. This is that guide.

There are three levels. Each one works on its own:

| Level | Needs | Time |
|---|---|---|
| 1. Run it offline | Python only | 2 min |
| 2. Run it live on Claude (Vertex AI) | A GCP project with Claude enabled | 15 min |
| 3. Run it caged (OpenShell + opencode) | Docker | 20 min |

---

## Level 1 — Run it offline (no cloud, no keys, right now)

```bash
git clone https://github.com/dhshah13/how-to-create-an-agent.git
cd how-to-create-an-agent
export DEMO_MOCK=1

python3 stage0_bare_call.py      # the chatbot
python3 stage1_harness.py        # the agent loop (posts unprompted!)
python3 stage2_guardrails.py     # type y/n at the approval gate
python3 stage3_workflow.py       # the same job as a pipeline
```

Mock mode replays scripted, deterministic model responses — the full demo arc with
zero credentials. Read the four stage files alongside; together they're ~150 lines
and that's the entire lesson.

---

## Level 2 — Run it live on Claude via Vertex AI

### Prerequisites

1. A **GCP project** with the **Vertex AI API enabled**.
2. A **Claude model enabled** in that project: Vertex AI console → **Model Garden**
   → search "Claude" → enable (your org admin may need to approve).
3. Your account (or a service account) holding **`roles/aiplatform.user`** on the
   project.
4. Python 3.10+ and the SDK: `pip3 install -r requirements.txt`

### Authenticate (pick one)

```bash
# Option A - your own Google account (recommended)
gcloud auth application-default login

# Option B - a service-account key file
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json

# Option C - a short-lived token (e.g. to use inside a container)
export ANTHROPIC_VERTEX_ACCESS_TOKEN=$(python3 mint_token.py)   # needs A or B on the host
```

### Configure and verify

```bash
export ANTHROPIC_VERTEX_PROJECT_ID=<your-project-id>
export CLOUD_ML_REGION=global            # or your org's pinned region, e.g. us-east5
export DEMO_MODEL=claude-opus-4-6        # whichever Claude your project has enabled

python3 check_setup.py
```

`check_setup.py` makes one tiny live call and tells you exactly what to fix if
anything's wrong (see Troubleshooting). When it prints `all good`, run the stages —
same commands as Level 1, without `DEMO_MOCK`.

**Which model do I have?** If `DEMO_MODEL` 404s, your project has a different
Claude enabled — try `claude-opus-4-8`, `claude-opus-4-6`, or `claude-sonnet-4-6`,
or check Model Garden. The code never hardcodes the model; it's always this env var.

---

## Level 3 — Run it caged (OpenShell sandbox + opencode cockpit)

The talk ran everything inside [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell)
(kernel-level per-binary network policy) with [opencode](https://opencode.ai) as the
cockpit. To reproduce that rig:

```bash
# install (needs Docker running)
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
openshell doctor check

# build the cage: create -> clone+install inside -> THEN lock down
openshell sandbox create --name agent-demo -- echo ready
openshell sandbox exec -n agent-demo -- bash -c \
  "cd /sandbox && git clone -q https://github.com/dhshah13/how-to-create-an-agent.git \
   && cd how-to-create-an-agent && pip3 install -q -r requirements.txt"
openshell policy set agent-demo --policy sandbox-policy.yaml
```

Then follow [GUIDE.md](GUIDE.md) Parts 2–3 for the two-window setup (cockpit +
cagecam), substituting your project ID. Notes for your environment:

- `sandbox-policy.yaml` pins **kernel-resolved binary paths** — if the sandbox
  image differs, re-resolve with `readlink -f $(which python3)` inside, and read
  denial reasons with `openshell logs agent-demo` (it names the exact binary and
  host that got blocked — that's your debugging loop).
- Inside the sandbox, authenticate the *stages* with a short-lived token
  (`mint_token.py` on the host → `.demo-env` inside). Use a key file only for
  opencode itself (its Node auth can't take bare tokens).
- Policy network rules hot-reload; give `policy set` ~10s before testing.

---

## Make it YOUR agent

The repo is a scaffold. Three files to touch, in order:

**1. `fake_tools.py` → your world.** Replace the fake data with your real reads
(slide 11's three swaps):

```python
def get_tickets() -> str:
    # was: canned JSON   ->   now: your Jira/Linear/GitHub query
def get_messages(channel=None) -> str:
    # was: canned chat   ->   now: your Slack/Teams read
def post_update(channel, text) -> str:
    # was: print()       ->   now: chat.postMessage - KEEP IT BEHIND THE GATE
```

Update `TOOLS` (the JSON schemas) to match — the **descriptions are prompts**: say
*when* to use each tool, not just what it does. Add tools the same way: schema +
implementation + a line in `run_tool()`.

**2. `stage2_guardrails.py` → your rules.** This file is the one you'll actually
deploy. Adapt the four guardrails to your domain:

- `ALLOWED_CHANNELS` → your allow-list of side-effect targets
- `validate()` → your facts: IDs that must exist, schemas, length, tone
- `ask_human()` → keep it. A human or an explicit signature approves every
  irreversible action. This is non-negotiable in week one.
- `MAX_ITERS` → your cost ceiling

**3. Then ask the slide-10 question: can you write the steps in advance?**
If yes — and for most reporting/routing jobs the answer is yes — copy
`stage3_workflow.py` instead: same tools, same validator, same gate, but the model
runs once inside `draft()`. Cheaper, debuggable, auditable. Build the agent loop
only for tasks where each step's outcome decides the next step.

**Before you ship either:** run your adversarial inputs (see `DEMO_SCRIPT.md` for
two that fool the model and bounce off the guardrails), and decide what your
equivalent of the sandbox is — the guardrails you wrote live *inside* the app;
something outside the process should hold the real blast-radius limits.

---

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `no Google credentials` | Run `gcloud auth application-default login`, or set `GOOGLE_APPLICATION_CREDENTIALS` |
| `403 PermissionDenied` on every model | Your principal lacks `roles/aiplatform.user` on the project — ask your admin |
| `404 Publisher Model ... not found` | That Claude model isn't enabled in this project/region — enable in Model Garden, try another `DEMO_MODEL`, or `CLOUD_ML_REGION=global` |
| `401` after ~1 hour (token mode) | Tokens expire — re-run `mint_token.py` |
| Works on host, hangs in a sandbox | The sandbox's default policy blocks python egress — apply `sandbox-policy.yaml`, then check `openshell logs` |
| No cloud access at all | `DEMO_MOCK=1` — everything runs offline |

Repo: https://github.com/dhshah13/how-to-create-an-agent · Slides + session: ask in
the channel where you got this link.
