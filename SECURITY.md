# Security Policy

Silicon Org is a research / harness project: a persistence layer for the
Dynamic Workflow agent pattern (graph, ledger, policy, runtime, learning). It
ships no network service and no hosted component — execution is local OSS only.
Please keep that scope in mind when assessing impact.

## Supported versions

Security fixes are provided for the current `0.7.x` line.

| Version | Supported |
|---------|-----------|
| 0.7.x   | ✅ |
| < 0.7   | ❌ |

## Reporting a vulnerability

Please report vulnerabilities **privately** — do not open a public issue.

Use GitHub's private vulnerability reporting:
**<https://github.com/zengury/silicon38/security/advisories/new>**
(Security → Advisories → *Report a vulnerability* on `zengury/silicon38`).

When you report, include where possible:

- affected file(s), command, or component
- reproduction steps or a proof of concept
- version / commit and your OS + Python version
- the impact you believe it has

## Response window

- **Acknowledgement:** within 5 business days.
- **Assessment & triage:** within 10 business days of acknowledgement.
- **Fix / disclosure:** coordinated with you once a fix or mitigation is ready;
  we will credit reporters who wish to be named.

## Scope notes

In-scope: the harness tooling (`tools/`, `runtime/`, `learning/`), the ontology
and registry loaders, and the optional LangGraph-native runtime.

Out of scope: behavior of third-party coding agents driving the Runtime, the
vendored offline visualizer assets under `visualizer/vendor/`, and issues that
require an already-compromised local machine.
