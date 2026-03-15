# Autonomous Memory Runtime

This document describes the autonomous runtime behavior of claw-memory-system inside OpenClaw.

## Goals
- standard
- portable
- safe by default
- low-touch day-to-day operation

## Runtime loops
### 1. Turn capture
- classify each turn
- queue pending memory candidates into `turn_candidates.json`
- default behavior is queue-only

### 2. Batch governance
- read governance drafts
- read pending turn candidates
- preview / merge / apply / noop / supersede
- refresh graph
- write reports

### 3. Future compact
- archive/supersede old tasks
- extract daily memory
- update MEMORY.md summaries

## Safe defaults
- `autoTurnCapture = false`
- `autoTurnQueueOnly = true`
- `turnCaptureMinConfidence = 0.88`
- `batchGovernanceEnabled = true`
- `batchGovernanceEvery = 6h`

Default principle:

> queue first, govern second, absorb third.

## Core stores
Located under `memory-system/stores/v2/`:
- `preferences.json`
- `tasks.json`
- `episodes.json`
- `skills.json`
- `session.json`
- `graph.json`
- `models.json`
- `migration_candidates.json`
- `skill_proposals.json`
- `turn_candidates.json`

## Release-safe lifecycle strategy
For v0.1, lifecycle wiring should remain queue-only.
The plugin may capture turns from a post-turn lifecycle hook such as `agent_end`, but it should not directly write structured memory by default.

## Recommended automation
- run batch governance every 6 hours
- observe reports before enabling turn capture
- only enable turn capture explicitly
