---
name: Feature request
about: Propose a new role, edge, tool, or capability
title: "[feature] "
labels: enhancement
assignees: ''
---

## Problem / motivation

What are you trying to do that the harness does not support today? What's the
pain?

## Proposed change

Describe the change. If it involves the role library, note which files it would
touch (see the Expansion Protocol in `org/REGISTRY.md`):

- [ ] Skill — `.agents/skills/<role>/SKILL.md`
- [ ] Harness profile — `org/registry/<role>.md`
- [ ] Ontology node — `ontology/nodes.yaml`
- [ ] Edges — `ontology/relations.yaml`
- [ ] Registry entry — `org/REGISTRY.md`
- [ ] Tooling / runtime / docs

## Alternatives considered

Other approaches you weighed and why you set them aside.

## Impact on invariants

Does this change role / edge / skill counts, add a relation type, or alter a
convergence gate? Note anything the audit would need to stay consistent with.

## Additional context

Links, prior art, related roles, or examples.
