## Analysis

### Problem Statement
The codebase at /Users/ZQ/roboease contains duplicated code, unclear module structure, and low maintainability/testability, which increases technical debt and slows development.

### Scope
**In scope:**
- Identify duplicate code patterns across the codebase
- Assess current module structure and propose improvements
- Evaluate test coverage and testability
- Provide recommendations for refactoring

**Out of scope:**
- Actual code changes or refactoring execution
- Performance optimization unrelated to maintainability
- Dependency upgrades or security fixes
- User-facing feature changes

### Recommended Agents
- `code-reviewer` (for duplicate detection and structural analysis)
- `test-architect` (for testability assessment)
- `refactoring-planner` (for actionable refactoring plan)

### Blocking Questions
- What is the primary programming language(s) in the codebase?
- Are there existing tests? If so, what framework?
- Is there a preferred module structure (e.g., feature-based, layered)?
- Are there any constraints (e.g., must maintain backward compatibility)?

### Priority
**High** – Duplicate code and poor structure compound over time, making future changes risky and slow. Early refactoring reduces long-term cost.