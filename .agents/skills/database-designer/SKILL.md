---
name: database-designer
description: Design schemas and migrations deliberately, with a rollback for every change and a measured justification for every index — use when a schema is created or modified, migrations are involved, or query performance is at stake.
---

## Purpose

Mastery of this skill produces schema and migration work that is safe to apply
to a production dataset and understandable years later. Schema decisions are the
hardest to reverse, so they are made deliberately: every column has a reason,
every index has a measured justification, and every forward migration ships with
the rollback written first. Normalization is the default; denormalization
happens only with measurement evidence and documented invariants.

## When to use

- A database schema is being created or modified.
- Migrations are involved and must be safe to run forward and back.
- Query performance is a concern that touches data modeling.
- Data modeling decisions or complex ORM relationships need to be made.

## Method

1. Model normalized first. Design to a normalized form by default. Only
   consider denormalizing when you have measurement evidence that normalization
   is the bottleneck, and then document the invariants that must be maintained
   manually as a consequence.
2. Justify every column and constraint. Each column exists for a stated reason.
   Each nullable column carries an explicit reason why nullable is correct;
   default to NOT NULL. Enforce referential integrity with real foreign key
   constraints at the database level, not only in application code.
3. Justify every index against a query. An index is added because a specific
   query pattern needs it, referenced concretely — never on general intuition.
   For queries over significant data volume, include the query plan.
4. Write the rollback before the forward migration ships. Every schema change
   has a corresponding down migration. The down operation is designed and
   verified as part of the same unit of work, not deferred.
5. Assess production locking. For any migration that could lock a table on a
   production-sized dataset, state the zero-downtime strategy — concurrent index
   builds, backfill in batches, expand-then-contract column changes — before it
   ships.
6. Validate syntax against the target database. Confirm the migration is
   syntactically valid for the actual engine and dialect in use.
7. Document the rationale. Record the schema reasoning, index justifications,
   and the rollback procedure so downstream engineers can implement models and
   operators can apply changes with confidence.

## Quality bar

- Every schema change has a corresponding rollback migration.
- No migration can lock a production table without a stated zero-downtime plan.
- Every index justification references a specific query pattern, not intuition.
- No nullable column exists without a stated reason nullable is correct.
- Foreign key constraints enforce referential integrity at the database level.
- Query plans are included for any query over significant data volume.

## Output

Migration file(s) containing both up and down operations for the target
database, plus an inline analysis covering the schema rationale, the index
justifications tied to query patterns, and the rollback procedure. The migration
is syntactically valid and every index maps to a concrete query.

## Anti-patterns

- Shipping a forward migration with no rollback path.
- Adding indexes on intuition rather than a measured, named query pattern.
- Denormalizing without evidence and without documenting the new invariants.
- Enforcing referential integrity only in application code, not the database.
- Running a table-locking migration on production with no downtime strategy.
