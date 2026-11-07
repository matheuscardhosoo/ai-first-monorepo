---
domain: "apps/web"
depends_on:
  - "apps/api-gateway"
  - "packages/common"
---

# Web Application Specification (apps/web/AGENTS.md)

This document is the localized context artifact for the deployable `apps/web` client application.

## 1. Domain Responsibility
The `apps/web` directory contains the primary single-page application (SPA / SSR):
- User interface presentation components and responsive design system.
- Client-side navigation, routing, and route guards.
- API client SDK integration consuming `apps/api-gateway`.
- State management and client-side form validations.

## 2. Invariants & Governance
1. **Never Import Database or Server Packages:** `apps/web` must NEVER import `packages/database`.
2. **Secure Token Storage:** Tokens received from authentication endpoints must be stored via secure HTTP-only cookies, not in raw `localStorage` vulnerable to XSS.
3. **Accessibility (a11y):** All UI elements must adhere to WCAG 2.1 AA accessibility guidelines.
