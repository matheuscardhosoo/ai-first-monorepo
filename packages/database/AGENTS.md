---
domain: "packages/database"
depends_on:
  - "packages/common"
---

# Database Domain Specification (packages/database/AGENTS.md)

This document is the localized context artifact for the `@monorepo/database` package.

## 1. Domain Responsibility
The `packages/database` package is the canonical owner of persistence, schema definitions, and database connectivity:
- PostgreSQL client configuration, connection pooling, and lifecycle management.
- Schema migrations and seed scripts.
- Unit-of-work transaction management (`runTransaction`).
- Generic base repository and query abstractions.

## 2. Public API Contract
The package exposes only the following public functions via `index.ts`:
- `createConnectionPool(config: DatabaseConfig): Pool`
- `runTransaction<T>(pool: Pool, callback: (client: Client) => Promise<T>): Promise<T>`
- `BaseRepository<T>`: Abstract class implementing standard CRUD interfaces.
- `healthCheck(pool: Pool): Promise<boolean>`

## 3. Invariants & Governance
1. **Parameterized Queries Only:** Raw SQL string interpolation or concatenation is strictly prohibited to prevent SQL injection.
2. **Migration Discipline:** Schema alterations must always use forward and backward migrations in `packages/database/migrations/`.
3. **Connection Cleanup:** Database clients checked out of the pool must be guaranteed to release in `finally` blocks.
4. **No Direct App Imports:** Apps must not access database connection pools directly if an API gateway or domain service exists.

## 4. Dependencies
- Allowed imports: `packages/common` (for logging and error definitions).
- Prohibited imports: `apps/*`, `packages/auth`.
