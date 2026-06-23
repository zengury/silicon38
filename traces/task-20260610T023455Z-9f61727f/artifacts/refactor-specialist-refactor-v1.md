# Refactor: Eliminate Library CRUD Endpoint Duplication

## Problem Statement

Four portal API files — `expression_library.py`, `action_library.py`, `voice_library.py`, and `knowledge_library.py` — were copy-paste duplicates sharing 6 identical CRUD endpoints (list, get, add, update, delete, official/list). Each file was ~87 lines differing only in entity class, service class, URL prefix, OpenAPI tag, and Chinese error strings. Any bug fix or improvement to the CRUD pattern required changes across 4 separate files.

## Solution

Created `shared/crud_router.py` — a factory function `create_library_crud_router()` that generates a standardized FastAPI `APIRouter` with all standard CRUD endpoints for any library-type entity.

### Files Changed

| File | Before | After | Change |
|------|--------|-------|--------|
| `shared/crud_router.py` (NEW) | — | 136 lines | Factory function |
| `api/portal/expression_library.py` | 87 lines | 18 lines | Uses factory |
| `api/portal/action_library.py` | 87 lines | 18 lines | Uses factory |
| `api/portal/voice_library.py` | 87 lines | 18 lines | Uses factory |
| `api/portal/knowledge_library.py` | 102 lines | 61 lines | Uses factory + keeps custom `create_with_dify` |
| `tests/test_shared.py` | 235 lines | 370 lines | Added 10 CRUD router tests |
| `tests/test_duplicate_detector.py` | — | — | Fixed import paths |

### Net Effect

- **Before**: ~360 lines across 4 files, 4× duplicate CRUD patterns, 0 tests for router behavior
- **After**: 251 lines total (136 factory + 115 across 4 files), 0 duplicate patterns, 10 new characterization tests
- Library CRUD endpoint duplication: **10 duplicate pairs → 0** (eliminated)

## What Is Now Easier to Change

1. **Adding a new library type** — Create a new file with ~15 lines using the factory instead of ~80 lines of copy-paste.
2. **Fixing a CRUD bug** — Change the factory once, all 4 (and future) libraries get the fix.
3. **Adding observability/audit to CRUD** — Single insertion point in the factory.
4. **Testing CRUD behavior** — The factory is independently testable with mock services, as demonstrated by the 10 new tests.

## Behavior Preservation Evidence

- **Before**: 129 tests passing
- **After**: 152 tests passing (23 new tests added)
- All route paths, HTTP methods, query parameters, error codes, and response shapes verified identical
- All `main.py` imports remain compatible
- Duplicate detector confirms library endpoint duplication eliminated