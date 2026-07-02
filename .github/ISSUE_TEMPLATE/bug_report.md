---
name: Bug report
about: Report something that is broken or behaves incorrectly
title: "[bug] "
labels: bug
assignees: ''
---

## Summary

A clear, concise description of the bug.

## Failing command

The exact command you ran (e.g. `python tools/audit.py`, `python
tools/langgraph_native_smoke.py`, `python tools/langgraph_run.py ...`):

```
<command here>
```

## `python tools/audit.py` output

Paste the relevant output. If the audit reports `INVALID`, include the listed
issues:

```
<audit output here>
```

## Expected behavior

What you expected to happen.

## Actual behavior

What actually happened (error messages, stack traces, wrong output).

## Environment

- OS:
- Python version (`python --version`):
- Silicon Org version / commit:
- Coding agent (Claude Code / Codex / Cursor / pi / other), if relevant:
- Installed with `pip install -e '.[langgraph-oss]'`? (yes/no)

## Additional context

Anything else that helps — ontology/registry changes in flight, custom roles,
partial traces, etc.
