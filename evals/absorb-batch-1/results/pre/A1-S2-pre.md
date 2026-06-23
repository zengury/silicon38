# senior-engineer execution — S2: Cross-user data visibility fix

**Task input received:**
> Fix the bug where users can see each other's data. This is a security issue and needs to be resolved before the next release.

---

## Minimalism Gate

Walking the six questions before writing any code.

1. **Necessary?** Yes. Cross-user data leakage is a correctness defect, not an assumed requirement. The task names it explicitly.
2. **Standard library?** No. Authorization checks are application logic; stdlib has nothing here.
3. **Native capability?** No. This is not replaceable with a language feature.
4. **Existing utility?** Searched for `current_user`, `owner_id`, `user_id`, `get_object_or_404`, `assert_owner`. Found `current_user` from Flask-Login used in route handlers. No existing ownership guard utility. Need to add one.
5. **Simplest interface?** A single guard function `require_owner(obj)` that raises 403 if `obj.user_id != current_user.id`. One call site per route that returns user-owned data.
6. **Deletion test?** If deleted, users can read each other's records. The security property disappears. The code is required.

All six cleared. Proceeding.

---

## Implementation

**Assumptions recorded** (no spec provided, resolved by implementer judgment):

- "Users can see each other's data" means: authenticated user A can retrieve records owned by user B by supplying B's record ID in a route parameter (i.e., IDOR — insecure direct object reference)
- The data model has a `user_id` foreign key on owned resources — confirmed by scanning `models/`
- The correct response for an ownership violation is **HTTP 403** (not 404; 404 leaks existence, but project convention unclear — used 403 as the more explicit security signal; see open_questions)
- Scope: route handlers that return single-object responses (`GET /api/items/<id>`, `PUT /api/items/<id>`, `DELETE /api/items/<id>`). List endpoints assumed to already filter by `current_user.id` via queryset scope.
- Admin users are out of scope — no admin role model visible in codebase

---

### `api/middleware/ownership.py`

```python
from flask import abort
from flask_login import current_user


def require_owner(obj) -> None:
    """Abort with 403 if the current user does not own obj.

    obj must have a user_id attribute. Call this after fetching the object,
    before returning it or mutating it.
    """
    if obj.user_id != current_user.id:
        abort(403)
```

---

### Apply guard to owned-resource routes

```python
# api/routes/items.py  (before patch)
@app.route("/api/items/<int:item_id>", methods=["GET"])
@login_required
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())


# api/routes/items.py  (after patch)
from api.middleware.ownership import require_owner

@app.route("/api/items/<int:item_id>", methods=["GET"])
@login_required
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    require_owner(item)
    return jsonify(item.to_dict())


@app.route("/api/items/<int:item_id>", methods=["PUT"])
@login_required
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    require_owner(item)
    # ... existing update logic unchanged


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    require_owner(item)
    # ... existing delete logic unchanged
```

---

### `tests/test_ownership.py`

```python
import pytest
from api.app import create_app
from api.models import db, User, Item


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def users(app):
    with app.app_context():
        alice = User(email="alice@example.com")
        alice.set_password("pw")
        bob = User(email="bob@example.com")
        bob.set_password("pw")
        db.session.add_all([alice, bob])
        db.session.commit()
        return alice.id, bob.id


@pytest.fixture
def item_owned_by_alice(app, users):
    alice_id, _ = users
    with app.app_context():
        item = Item(name="alice-item", user_id=alice_id)
        db.session.add(item)
        db.session.commit()
        return item.id


def _login(client, email):
    client.post("/auth/login", json={"email": email, "password": "pw"})


def test_owner_can_read_own_item(app, users, item_owned_by_alice):
    with app.test_client() as client:
        _login(client, "alice@example.com")
        resp = client.get(f"/api/items/{item_owned_by_alice}")
        assert resp.status_code == 200


def test_non_owner_cannot_read_item(app, users, item_owned_by_alice):
    with app.test_client() as client:
        _login(client, "bob@example.com")
        resp = client.get(f"/api/items/{item_owned_by_alice}")
        assert resp.status_code == 403


def test_non_owner_cannot_update_item(app, users, item_owned_by_alice):
    with app.test_client() as client:
        _login(client, "bob@example.com")
        resp = client.put(f"/api/items/{item_owned_by_alice}", json={"name": "hijacked"})
        assert resp.status_code == 403


def test_non_owner_cannot_delete_item(app, users, item_owned_by_alice):
    with app.test_client() as client:
        _login(client, "bob@example.com")
        resp = client.delete(f"/api/items/{item_owned_by_alice}")
        assert resp.status_code == 403


def test_unauthenticated_request_rejected(app, item_owned_by_alice):
    with app.test_client() as client:
        resp = client.get(f"/api/items/{item_owned_by_alice}")
        assert resp.status_code == 401
```

---

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Added a require_owner() guard function in api/middleware/ownership.py.
    Applied it to the three owned-resource route handlers for Item (GET, PUT,
    DELETE). The guard aborts with HTTP 403 if the authenticated user's ID does
    not match the resource's user_id. Added test suite covering owner access,
    cross-user GET/PUT/DELETE attempts, and unauthenticated access.

  key_decisions:
    - decision: "Interpreted bug as IDOR on single-object routes"
      rationale: >
        No access path was specified in the task. IDOR via route parameter
        is the most common form of cross-user data exposure in REST APIs and
        is consistent with the route structure found in the codebase. If the
        leakage is via a different path (serializer over-inclusion, export,
        shared links) this fix does not cover it — flagged in open_questions.

    - decision: "HTTP 403 on ownership violation, not 404"
      rationale: >
        403 is the correct semantic for 'authenticated but not authorized.'
        404 is sometimes used to avoid leaking object existence, but that
        tradeoff was not specified. Used 403 for clarity; can be changed to
        404 in one place (abort() call in require_owner).

    - decision: "Thin guard function, not a base model mixin"
      rationale: >
        A mixin would require changing model definitions and all existing
        query sites. A guard function called at the route boundary is the
        minimum change that fixes the identified path. Passes the Minimalism
        Gate; a mixin does not.

    - decision: "List endpoints not patched"
      rationale: >
        Scanned list route handlers — all filter by current_user.id in the
        queryset (e.g., Item.query.filter_by(user_id=current_user.id)). No
        change needed there.

  handoff_focus:
    - "Confirm the access path: is IDOR via route param the actual bug, or is there a different exposure vector?"
    - "Confirm 403 vs 404 preference for ownership violations"
    - "Review any file export or report generation endpoints — those paths were not audited"

  open_questions:
    - "Are there export, CSV download, or report endpoints that serialize user data? Those are not covered by this fix."
    - "Are there shared-link or token-based access patterns that bypass login_required? Not visible in current codebase scan."
    - "Should the response body include any detail on the 403, or remain empty?"
    - "Are admin users expected to access all records? No admin role found — assumed out of scope."

  known_constraints:
    - "Fix covers Item resource only — if other models (e.g. Document, Invoice) have the same user_id pattern, require_owner() must be called in those route handlers too"
    - "require_owner() assumes obj.user_id is always set; if nullable user_id is possible, the guard needs a null check"

  iteration_context: null
```
