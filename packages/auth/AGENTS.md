---
domain: "packages/auth"
depends_on:
  - "packages/common"
---

# Auth Domain Specification (packages/auth/AGENTS.md)

This document is the localized context artifact for the `@monorepo/auth` package. All agents working within `packages/auth` must adhere to these domain rules and boundaries.

## 1. Domain Responsibility
The `packages/auth` package owns all authentication and authorization logic:
- JWT token generation, cryptographic signing, and verification.
- HTTP Authentication Middleware for API gateways and service endpoints.
- Role-Based Access Control (RBAC) permission evaluation.
- Secure password hashing and credential verification.

## 2. Public API Contract
The package exposes only the following public functions via `index.ts`:
- `signToken(payload: AuthUser, secret: string, expiresIn: string): string`
- `verifyToken(token: string, secret: string): TokenPayload`
- `authMiddleware(options: AuthOptions): RequestHandler`
- `hashPassword(password: string): Promise<string>`
- `verifyPassword(password: string, hash: string): Promise<boolean>`
- `checkPermission(role: Role, requiredPermission: Permission): boolean`

## 3. Security & Invariant Rules
1. **Zero Plaintext Passwords:** Passwords must be hashed with Argon2id or Bcrypt before persistence.
2. **Short-Lived Access Tokens:** Access tokens must not exceed a 15-minute lifespan. Refresh tokens must use rotation.
3. **Strict Validation:** Auth middleware must reject malformed bearer tokens with HTTP 401 Unauthorized before any upstream routing.
4. **Mocked I/O in Unit Tests:** All unit tests must mock external key providers and timestamp generators.

## 4. Dependencies
- Allowed imports: `packages/common` (for custom error hierarchy and logger).
- Prohibited imports: `apps/*`, `packages/database` (database queries must be performed via caller-injected repositories).
