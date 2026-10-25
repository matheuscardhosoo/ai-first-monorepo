# Packages Directory

This directory contains reusable business domains, shared core logic, data contracts, and utility libraries.

## Architectural Rules
1. **Never Import from Apps:** Packages must **NEVER** import from `apps/`.
2. **No Circular Package Dependencies:** Circular dependencies between packages are forbidden.
3. **Public Contract Encapsulation:** Packages must expose a clean public interface and hide internal implementation details.
4. **Isolated Unit Testing:** All unit tests in `packages/` must mock external I/O (no databases, real HTTP calls, or file system dependencies).
