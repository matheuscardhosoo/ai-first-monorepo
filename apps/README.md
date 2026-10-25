# Apps Directory

This directory contains deployable end-user applications, services, and CLIs.

## Architectural Rules
1. **Unidirectional Import:** Apps may import reusable libraries from `packages/`.
2. **Encapsulated Dependencies:** Each app must have its own dependency manifest (e.g. `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`).
3. **Integration & E2E Testing:** Apps are the home for end-to-end user journey tests and integration tests.
