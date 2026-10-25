# ADR 0001: Record Architecture Decisions

## Status
Accepted

## Context
In an AI-first monorepo, autonomous agents and human developers make architectural decisions that shape domain boundaries, language choices, communication patterns, and dependencies. Without a persistent record of decisions, agents suffer from architectural amnesia and drift.

## Decision
We will store all major architectural decisions in `docs/adr/` as Architecture Decision Records (ADRs). Each record will describe:
1. Context and Problem Statement
2. Options Considered
3. Decision Made and Rationale
4. Consequences (Positive and Negative)

## Compliance & Enforcement
- Skill 02 (Technical Design) must consult existing ADRs before proposing new patterns.
- Skill 05 (Code Review) and Skill 07 (Continuous Evaluator) verify code against ADR compliance.
