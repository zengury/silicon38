# Model Selection Policy

Silicon Org does not hard-code provider-specific model IDs into the graph.
Users may run the Runtime with Claude, Codex, local models, or another agent
stack, and each stack names models differently.

By default, every node uses the Runtime's current/default model. The layer
guidance below is advisory: it describes the kind of model that fits the work,
not a required model name.

If a deployment wants concrete provider/model overrides, keep them in local
`org/models.local.yaml`. They are deployment policy, not graph policy, and
must not be read by `ontology/nodes.yaml` or the scheduler.

---

## Recommended Model Profiles

| Layer | Work kind | Suitable model profile | Why |
|-------|-----------|------------------------|-----|
| Runtime | Graph control, conflict resolution, decoding | strongest available reasoning model | Holds global state and makes routing judgments |
| Layer 1 | Intake, classification, context mapping | fast/low-latency model with adequate reasoning | High-frequency, bounded analysis |
| Layer 2 | Architecture, implementation, design, ops | balanced coding/design model | Produces primary deliverables |
| Layer 3 | Review, challenge, audit, release judgment | strongest review/reasoning model available | Lower frequency, higher consequence |

If the user has not configured models, do not invent aliases or version IDs.
Use the Runtime default and state the recommended profile in the node preview.

## Optional Local Configuration

Users can add `org/models.local.yaml` to map profiles or roles to their own
models. This file is intentionally local policy and should not be required by
the ontology.

Example:

```yaml
schema: silicon_org.model_routing.v1

default:
  provider: runtime
  model: runtime-default
  reasoning_effort: inherit

runner_pools:
  api_model:
    provider: deepseek
    model: deepseek-chat
    reasoning_effort: medium
    session_policy: ephemeral
  coding_builder:
    provider: pi
    model: runtime-default
    reasoning_effort: medium
    session_policy: warm
  coding_reviewer:
    provider: pi
    model: runtime-default
    reasoning_effort: high
    session_policy: warm
  frontend_browser:
    provider: pi
    model: runtime-default
    reasoning_effort: medium
    session_policy: warm

profiles:
  fast_reasoning:
    provider: your-provider
    model: your-fast-model
    reasoning_effort: low
  implementation:
    provider: your-provider
    model: your-coding-model
    reasoning_effort: medium
  security_high_reasoning:
    provider: your-provider
    model: your-security-review-model
    reasoning_effort: high

roles:
  senior-engineer:
    runner_pool: coding_builder
  senior-frontend:
    runner_pool: frontend_browser
  security-engineer:
    runner_pool: coding_reviewer
  code-reviewer:
    runner_pool: coding_reviewer
```

Resolution order:
1. `roles.<role>.runner_pool` — exact role mapped to a reusable pool
2. `roles.<role>` — exact per-node provider/model override
3. `harness_profiles.<role>.execution.default_runner_pool` if present
4. inferred runner pool from harness tools/write scope
5. `profiles.<harness_profiles[role].model_profile>` — capability profile
6. `default`
7. Runtime current/default model

Per-node role overrides are first-class. A deployment may run every node on a
different provider/model as long as the node still obeys its harness, tool
permissions, context report contract, and Ledger commit rules.

API keys do not belong in committed files. Configure them as environment
variables. Direct DeepSeek execution uses:

```bash
export DEEPSEEK_API_KEY="..."
```

For a machine-local persistent key, create ignored file `org/.env.local`:

```bash
DEEPSEEK_API_KEY=...
```

`provider: deepseek` calls the DeepSeek API directly. `provider: pi` dispatches
to the local `pi` CLI and should normally use `model: runtime-default`, so pi
uses its own configured coding model instead of receiving a forced model id.

## Runtime Behavior

When activating a node, the Runtime may ask the user whether they want to
configure model overrides. If no answer or config is available, proceed with
the Runtime default model and record only the recommended profile.

External spawners should surface both:
- the resolved model if configured
- the recommended profile if not configured

They must not treat any provider-specific model name as mandatory.
