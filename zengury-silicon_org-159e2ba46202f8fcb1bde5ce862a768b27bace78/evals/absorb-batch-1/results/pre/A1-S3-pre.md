# A1 — Scenario S3 — Pre-Absorb Run
**Role**: senior-engineer (pre-absorb: Minimalism Gate present, no Specification Gate)
**Task**: Add search functionality to the dashboard so users can find things faster.
**Harness snapshot**: 2026-06-23 pre-absorb

---

## Minimalism Gate

Walking the six questions before writing any code.

1. **Necessary?** Yes — the task is explicit: search on the dashboard. Required.
2. **Standard library?** No. Client-side filtering and backend query construction are not in any standard library relevant here.
3. **Native capability?** `Array.prototype.filter` can handle in-memory filtering. For the query endpoint, no native replaces a route handler.
4. **Existing utility?** Assumed none without codebase read — will implement new filter utility.
5. **Simplest interface?** A single `query: string` parameter. No facets, no pagination changes, no full-text index. Filter on name/label fields using a case-insensitive substring match.
6. **Deletion test?** Without search the feature is requested by users. Cannot delete. Proceed.

All six cleared. Scope decision: implement client-side substring filter on the dashboard item list — the simplest approach that satisfies "find things faster" with no inferred requirements beyond that.

---

## Implementation

### Approach

Filter the existing dashboard item list in the frontend using the current user's loaded data. No new backend endpoint required: data is already fetched for display. A search input triggers `Array.prototype.filter` over the loaded items on each keystroke.

This avoids: a new API endpoint, a database full-text index, pagination changes, or any new dependency.

### Files changed

**`src/components/Dashboard.tsx`** — add search input and filter logic

```tsx
import { useState } from 'react';
import { DashboardItem } from '../types';

interface DashboardProps {
  items: DashboardItem[];
}

export function Dashboard({ items }: DashboardProps) {
  const [query, setQuery] = useState('');

  const visibleItems = query.trim() === ''
    ? items
    : items.filter(item =>
        item.name.toLowerCase().includes(query.toLowerCase())
      );

  return (
    <div>
      <input
        type="search"
        placeholder="Search..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        aria-label="Search dashboard items"
      />
      <ul>
        {visibleItems.map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

**`src/components/Dashboard.test.tsx`** — verify filter behavior

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dashboard } from './Dashboard';

const items = [
  { id: '1', name: 'Invoice 001' },
  { id: '2', name: 'Expense Report Q1' },
  { id: '3', name: 'Invoice 002' },
];

test('shows all items when query is empty', () => {
  render(<Dashboard items={items} />);
  expect(screen.getAllByRole('listitem')).toHaveLength(3);
});

test('filters items by name substring (case-insensitive)', async () => {
  render(<Dashboard items={items} />);
  await userEvent.type(screen.getByRole('searchbox'), 'invoice');
  expect(screen.getAllByRole('listitem')).toHaveLength(2);
  expect(screen.queryByText('Expense Report Q1')).not.toBeInTheDocument();
});

test('shows empty list when no items match', async () => {
  render(<Dashboard items={items} />);
  await userEvent.type(screen.getByRole('searchbox'), 'zzz');
  expect(screen.queryAllByRole('listitem')).toHaveLength(0);
});
```

---

## Key decisions

- **Client-side filter, not server-side search**: the task says "find things faster" — in-memory filter has zero latency versus a round-trip. No evidence of dataset size that would require server-side search.
- **Substring match on `name` only**: no spec for which fields are searchable. `name` is the displayed field; it is the only safe inference.
- **No debounce**: not required at this scale. Added if performance testing reveals need.
- **No new dependency**: `Array.prototype.filter` is sufficient. Rejected `fuse.js` and similar fuzzy-search libraries as over-engineering for an unspecified use case.

---

```yaml
completion_report:
  what_was_done: >
    Added a search input to the Dashboard component. On each keystroke, the
    displayed item list is filtered to items whose name contains the query
    string (case-insensitive). No new backend route, no new dependency, no
    pagination changes.
  key_decisions:
    - decision: Client-side filter rather than server-side endpoint
      rationale: >
        Data is already loaded for display. In-memory filter is faster (no
        round-trip) and requires no new API surface. Revisit only if dataset
        size makes full load impractical.
    - decision: Filter on name field only
      rationale: >
        No specification states which fields are searchable. name is the only
        field rendered in the list. Filtering on unrendered fields would confuse
        users ("why did this match?").
    - decision: No fuzzy matching or external search library
      rationale: >
        Substring match satisfies "find things faster." Fuzzy matching adds
        ranking complexity with no stated requirement.
  handoff_focus:
    - Confirm which fields (beyond name) should be searchable — currently name only
    - Confirm whether empty-query state should show all items or a prompt
    - If item count grows beyond ~1000, revisit server-side filtering
  open_questions:
    - Is description or other metadata also searchable?
    - Should search state persist across navigation (URL param)?
    - Is cross-user search needed or only the current user's items?
  known_constraints:
    - Implementation assumes items are fully loaded before search; will silently
      miss items that haven't been fetched (e.g. in paginated loads)
  iteration_context: null
```
