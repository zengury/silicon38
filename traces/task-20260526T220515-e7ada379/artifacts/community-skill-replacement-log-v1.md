# Community Skill Replacement Log

Date: 2026-05-27
Operator: Runtime acting on user instruction: replace first, optimize gradually.

## Replacement Strategy

To avoid conflicts with parallel work, existing local skill directories were not
overwritten. Community candidates were copied into new `community-*` skill
directories, and `ontology/nodes.yaml` was updated to point selected nodes at
those new directories.

This keeps previous local skills available for comparison, rollback, and later
benchmarking.

## Nodes Replaced

| Role | New `skill_ref` | Source |
|---|---|---|
| `zoom-out` | `.agents/skills/community-alirez-codebase-onboarding` | `alirezarezvani/claude-skills` |
| `caveman` | `.agents/skills/community-julius-caveman` | `JuliusBrussee/caveman` |
| `refactor-specialist` | `.agents/skills/community-dimillian-review-and-simplify-changes` | `Dimillian/Skills` |
| `observability-engineer` | `.agents/skills/community-alirez-observability-designer` | `alirezarezvani/claude-skills` |
| `performance-engineer` | `.agents/skills/community-alirez-performance-profiler` | `alirezarezvani/claude-skills` |
| `ui-design-system` | `.agents/skills/community-alirez-ui-design-system` | `alirezarezvani/claude-skills` |
| `delivery-prover` | `.agents/skills/community-lackey-playwright-skill` | `lackeyjb/playwright-skill` |
| `customer-success` | `.agents/skills/community-alirez-customer-success-manager` | `alirezarezvani/claude-skills` |
| `graph-topologist` | `.agents/skills/community-dimillian-project-skill-audit` | `Dimillian/Skills` |
| `grill-me` | `.agents/skills/community-alirez-challenge` | `alirezarezvani/claude-skills` |
| `dependency-auditor` | `.agents/skills/community-alirez-dependency-auditor` | `alirezarezvani/claude-skills` |
| `technical-writer` | `.agents/skills/community-composio-content-research-writer` | `ComposioHQ/awesome-codex-skills` |
| `handoff` | `.agents/skills/community-alirez-handoff` | `alirezarezvani/claude-skills` |

## Not Replaced Yet

`prototype` remains on `.agents/skills/prototype`.

Reason: available community candidates were adjacent, not direct. Playwright and
webapp-testing skills prove running UI behavior; they do not define prototype
strategy, throwaway boundaries, or feasibility-validation output. Replacing it
now would weaken role semantics.

## Known Follow-Up Optimization

- `caveman`: node title says "First Principles Analyst" but the community
  candidate is a compression-mode skill. Decide whether to rename/scope the
  node or recruit a true first-principles simplifier.
- `handoff`: community candidate is a strong session handoff skill, but it does
  not yet encode Silicon Org's required digest-linked context block chain.
- `graph-topologist`: community candidate audits project skills and sessions;
  it is not yet a native Silicon trace topologist.
- `technical-writer`: current replacement is broader content/research writing,
  not exact API/maintainer documentation. Recruit a more exact candidate.
- `delivery-prover`: Playwright candidate is strongest for web/browser proof.
  CLI/API proof still needs extension.

## Verification

`python3 tools/audit.py` -> `VALID`
