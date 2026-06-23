# A2 — Scenario S1 — Pre-Absorb Run
**Role**: api-designer (pre-absorb: no MCP Server Design section)
**Task**: Design an API for a GitHub integration that an AI coding assistant will use. The assistant needs to read PRs, check CI status, read files, and create branches. The integration will run locally on the developer's machine.
**Harness snapshot**: 2026-06-23 pre-absorb

---

## API Contract

### Core types

```typescript
// ── Identity types ──────────────────────────────────────────────────────────

/** Owner is a GitHub org or user login. */
type Owner = string;
type Repo  = string;
type Sha   = string;
type BranchName = string;

// ── Pull Request ─────────────────────────────────────────────────────────────

type PRState = 'open' | 'closed' | 'merged';

interface PullRequest {
  number:    number;
  title:     string;
  body:      string | null;
  state:     PRState;
  headBranch: BranchName;
  baseBranch: BranchName;
  headSha:   Sha;
  authorLogin: string;
  isDraft:   boolean;
  createdAt: string;  // ISO-8601
  updatedAt: string;  // ISO-8601
}

interface ListPRsParams {
  owner:  Owner;
  repo:   Repo;
  state?: PRState;          // default: 'open'
  limit?: number;           // default: 30, max: 100
}

interface PRFileSummary {
  path:      string;
  additions: number;
  deletions: number;
  status:    'added' | 'modified' | 'removed' | 'renamed';
}

interface PRDetail extends PullRequest {
  changedFiles: PRFileSummary[];
  reviewDecision: 'approved' | 'changes_requested' | 'pending' | null;
}

// ── CI / Check Runs ──────────────────────────────────────────────────────────

type CheckStatus   = 'queued' | 'in_progress' | 'completed';
type CheckConclusion = 'success' | 'failure' | 'neutral' | 'cancelled'
                     | 'skipped' | 'timed_out' | null;  // null when not yet completed

interface CheckRun {
  id:          number;
  name:        string;
  status:      CheckStatus;
  conclusion:  CheckConclusion;
  startedAt:   string | null;   // ISO-8601; null if queued
  completedAt: string | null;   // ISO-8601; null if not done
  detailsUrl:  string;
}

interface CheckSuite {
  runs:           CheckRun[];
  overallStatus:  CheckStatus;
  /** null when any run is still in_progress/queued */
  overallConclusion: CheckConclusion;
}

// ── File Contents ────────────────────────────────────────────────────────────

interface FileContents {
  path:     string;
  content:  string;   // UTF-8 decoded; binary files not supported
  encoding: 'utf-8';
  sha:      Sha;
  size:     number;   // bytes
}

interface GetFileParams {
  owner:  Owner;
  repo:   Repo;
  path:   string;
  ref?:   BranchName | Sha;   // default: repo default branch
}

// ── Branches ─────────────────────────────────────────────────────────────────

interface Branch {
  name:    BranchName;
  headSha: Sha;
}

interface CreateBranchParams {
  owner:    Owner;
  repo:     Repo;
  name:     BranchName;
  fromRef:  BranchName | Sha;  // required; prevents silent default-branch assumption
}

// ── Errors ───────────────────────────────────────────────────────────────────

type GitHubErrorCode =
  | 'NOT_FOUND'
  | 'PERMISSION_DENIED'
  | 'RATE_LIMITED'
  | 'BRANCH_ALREADY_EXISTS'
  | 'BINARY_FILE'
  | 'FILE_TOO_LARGE'
  | 'NETWORK_ERROR';

interface GitHubError {
  code:    GitHubErrorCode;
  message: string;   // human-readable, not for programmatic branching
}

type Result<T> = { ok: true; value: T } | { ok: false; error: GitHubError };

// ── Client interface ─────────────────────────────────────────────────────────

interface GitHubClient {
  /** List open (or filtered) pull requests for a repository. */
  listPullRequests(params: ListPRsParams): Promise<Result<PullRequest[]>>;

  /** Fetch full PR detail including changed files and review decision. */
  getPullRequest(owner: Owner, repo: Repo, number: number): Promise<Result<PRDetail>>;

  /** Get all check runs for a given commit SHA. */
  getCheckSuite(owner: Owner, repo: Repo, ref: Sha | BranchName): Promise<Result<CheckSuite>>;

  /** Read a single file's content at an optional ref. Binary files return BINARY_FILE error. */
  getFileContents(params: GetFileParams): Promise<Result<FileContents>>;

  /** Create a branch from the given ref. Fails fast with BRANCH_ALREADY_EXISTS if name is taken. */
  createBranch(params: CreateBranchParams): Promise<Result<Branch>>;
}
```

---

## Design rationale

### Nullable vs. non-nullable

- `PullRequest.body` is `string | null` — GitHub allows PRs with no body; callers must handle null rather than receiving an empty string that looks like content.
- `CheckRun.startedAt` / `completedAt` are `string | null` — a queued run has no start time; encoding as `null` forces callers to check rather than parse a sentinel string like `""`.
- `CheckConclusion` includes `null` — `null` means "not yet determined" and is structurally distinct from `'neutral'`. Conflating them produces silent logic errors in CI-gating code.

### Synchronous vs. async

All methods return `Promise<Result<T>>`. GitHub calls are network I/O; there is no meaningful synchronous variant. `Result<T>` is chosen over thrown exceptions because the caller (an AI assistant) will compose multiple calls sequentially and needs to handle errors inline without try/catch nesting.

### Positional vs. named parameters

Methods that take more than two arguments use a params object (`ListPRsParams`, `GetFileParams`, `CreateBranchParams`). Two-argument calls (`getPullRequest`, `getCheckSuite`) use positional parameters — they are unambiguous at the call site and a params object would add noise.

### `fromRef` is required on `createBranch`

A common mistake is creating a branch without stating its source, silently branching from HEAD of the default branch. Making `fromRef` required forces the caller to express intent. This is particularly important for an AI caller that may have an older SHA in context.

### Error taxonomy

`GitHubErrorCode` is a union of string literals, not a subclass hierarchy. This means callers can exhaustively switch on error codes without an `instanceof` chain. `BINARY_FILE` and `FILE_TOO_LARGE` are first-class codes because an AI caller will frequently attempt to read source files and must distinguish "file doesn't exist" from "file exists but is not readable as text."

### What is not in this API

- **Mutation of PRs** (approve, comment, merge): not in scope per task.
- **Repository creation or fork**: not in scope.
- **Pagination cursor**: `limit` caps at 100 which covers the common AI assistant use case (scan open PRs, find relevant ones). Full pagination adds interface complexity that the stated need does not require.
- **Authentication**: out of scope for this contract. Assumed to be injected at construction time (token or app credentials), not passed per-call.

### Versioning

This is an internal integration — no public versioning strategy is required. If this becomes a shared library consumed by other tools, semantic versioning with a changelog should be applied at the package level.

---

## Usage examples

```typescript
const client: GitHubClient = createGitHubClient({ token: process.env.GITHUB_TOKEN });

// Find open PRs mentioning a file path
const prsResult = await client.listPullRequests({ owner: 'acme', repo: 'api', state: 'open' });
if (!prsResult.ok) {
  console.error(prsResult.error.code); // handle RATE_LIMITED, PERMISSION_DENIED, etc.
  return;
}

for (const pr of prsResult.value) {
  const detail = await client.getPullRequest('acme', 'api', pr.number);
  if (detail.ok && detail.value.changedFiles.some(f => f.path === 'src/auth.ts')) {
    console.log(`PR #${pr.number} touches auth.ts`);
  }
}

// Read a file at the PR head
const file = await client.getFileContents({
  owner: 'acme', repo: 'api', path: 'src/auth.ts', ref: pr.headSha
});
if (!file.ok && file.error.code === 'BINARY_FILE') {
  console.log('Cannot read binary file');
}

// Create a working branch
const branch = await client.createBranch({
  owner: 'acme', repo: 'api', name: 'fix/auth-check', fromRef: 'main'
});
if (!branch.ok && branch.error.code === 'BRANCH_ALREADY_EXISTS') {
  console.log('Branch already exists, resuming');
}

// Check CI on a branch
const ci = await client.getCheckSuite('acme', 'api', 'fix/auth-check');
if (ci.ok && ci.value.overallConclusion === 'failure') {
  const failed = ci.value.runs.filter(r => r.conclusion === 'failure');
  console.log('Failing checks:', failed.map(r => r.name));
}
```

---

## Breaking change assessment

This is a new interface — no existing contract. No breaking changes. If `GitHubClient` is shipped and then changed:

- Removing or renaming any method is a breaking change.
- Narrowing an existing parameter type (e.g., removing `Sha` from `ref`) is breaking.
- Widening a return type union (adding new `GitHubErrorCode` values) is technically breaking for exhaustive switches; document new codes in a changelog.

---

```yaml
completion_report:
  what_was_done: >
    Designed a TypeScript GitHubClient interface covering the four stated
    capabilities: list/read PRs, check CI status, read file contents, create
    branches. All error conditions are typed via a Result<T> wrapper and a
    GitHubErrorCode union. Nullable fields are explicit with rationale.
  key_decisions:
    - decision: Result<T> discriminated union over thrown exceptions
      rationale: >
        Callers composing multiple sequential calls benefit from inline error
        handling. Thrown exceptions require try/catch at every call site or
        a single catch that cannot distinguish error types.
    - decision: fromRef required on createBranch
      rationale: >
        Silent default-branch assumption is a common source of incorrect
        branches. Making source explicit eliminates the footgun.
    - decision: Binary file as first-class error code
      rationale: >
        An AI caller will commonly attempt to read any file it encounters.
        Returning a typed BINARY_FILE error lets the caller decide to skip
        rather than receive garbled content or a generic error.
    - decision: No pagination cursor
      rationale: >
        limit: 100 covers the realistic AI assistant workflow (scan open PRs).
        Full cursor pagination adds interface surface the task does not require.
  handoff_focus:
    - Authentication injection pattern should be decided before senior-engineer
      implements the client constructor
    - Rate limit backoff strategy is not in the interface — implementer must
      decide whether to retry transparently or surface RATE_LIMITED to the caller
  open_questions:
    - Should getFileContents support tree listing (directory) or only file paths?
    - Is pagination needed for repositories with >100 open PRs?
  known_constraints:
    - Binary file detection relies on GitHub API response; large text files
      (>1MB) are also rejected via FILE_TOO_LARGE to avoid context overload
  iteration_context: null
```
