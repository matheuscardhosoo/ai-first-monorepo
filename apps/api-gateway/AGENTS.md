---
domain: "apps/api-gateway"
depends_on:
  - "packages/auth"
  - "packages/common"
  - "packages/database"
---

# API Gateway Application Specification (apps/api-gateway/AGENTS.md)

This document is the localized context artifact for the deployable `apps/api-gateway` service.

## 1. Domain Responsibility
The API Gateway is the public ingress service into the monorepo ecosystem:
- HTTP request routing and reverse proxying to internal domain services.
- Global middleware pipeline execution:
  1. Request ID & Structured Logger (`packages/common`)
  2. Rate Limiting (Token Bucket / Redis)
  3. Authentication Middleware (`packages/auth`)
  4. CORS & Security Headers
- OpenAPI / Swagger documentation aggregation.

## 2. Invariants & Governance
1. **Unidirectional Import Rule:** `apps/api-gateway` can import from `packages/auth`, `packages/common`, and `packages/database`.
2. **Stateless Scalability:** The gateway must remain completely stateless to support horizontal autoscaling behind a cloud load balancer.
3. **Graceful Shutdown:** Process must intercept `SIGTERM` and `SIGINT` to drain in-flight HTTP connections within a 15-second grace period.
