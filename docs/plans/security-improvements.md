# Security Improvements Plan

## Overview
This plan addresses the findings from the repo review and hardens authentication, readiness error handling, rate limiting, and test coverage. It is scoped to fixes that are low-risk and align with the current project architecture.

## Goals
- Ensure inactive users cannot authenticate through any login path.
- Avoid leaking internal error details in readiness responses.
- Make rate limiting consistent across multi-worker deployments.
- Align documentation with actual dev/test workflows.
- Add regression tests for authentication and token revocation behavior.

## Findings (Recap)
1. `/auth/login/form` bypasses `is_active` checks.
2. Readiness endpoint returns raw DB exception details.
3. Rate limiting uses per-process in-memory backend (not shared across workers).
4. README claims `make test` runs in Docker, but Makefile runs locally.
5. Redis mock cannot async-iterate `scan_iter`, masking issues in token revocation.

## Plan

### Phase 1 — Authentication Hardening
- [ ] Enforce `is_active` check in `/auth/login/form` to match `/auth/login`.
- [ ] Add tests to ensure inactive users are rejected via both login paths.

### Phase 2 — Safer Readiness Error Handling
- [ ] Replace raw DB error message with a generic response (`"not ready"`).
- [ ] Log the underlying exception at server side (structured logging).
- [ ] Add tests to ensure readiness does not include exception detail.

### Phase 3 — Rate Limiting Consistency
- [ ] Configure slowapi to use Redis storage in production for shared rate limits.
- [ ] Add settings (e.g., `RATE_LIMIT_REDIS_URL`) or reuse `REDIS_URL` with a clear toggle.
- [ ] Document expected behavior and deployment guidance in README.

### Phase 4 — Testing Improvements
- [ ] Fix Redis mock `scan_iter` to behave as an async iterator.
- [ ] Add tests for refresh token revocation (`logout` + refresh should fail).
- [ ] Add tests for `revoke_all_user_tokens` on password change.

### Phase 5 — Documentation Alignment
- [ ] Update README to reflect how `make test` is executed.
- [ ] Clarify Docker vs local workflows for tests and linting.

## Deliverables
- Code changes in `app/api/v1/auth.py`, `app/api/v1/health.py`, `app/core/limiter.py`, and tests.
- Updated README sections for commands and testing guidance.
- New or updated configuration options for rate limiter storage backend.

## Out of Scope
- OAuth providers and external auth flows.
- Extended audit logging or SIEM integrations.
- Multi-tenant rate-limiting policies.

## Acceptance Criteria
- Inactive users cannot authenticate on any login endpoint.
- Readiness responses never include internal DB exception strings.
- Rate limiting is shared across processes when configured for Redis.
- Tests cover login status, logout/refresh revocation, and token invalidation.
- README accurately reflects how to run tests.
