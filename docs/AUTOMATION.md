# Automation foundation

## While open

Settings → “Triage while the app is open” checks unprocessed imported messages every minute. The shared triage engine classifies each once and creates at most one reply draft per interview message. Reminders show an in-app toast once per session and can be snoozed. No account sync or remote action runs on a timer.

## Offline worker

Node 20+ can process a JSON inbox drop without opening the browser:

```sh
node worker.mjs intake.json workspace-backup.json
```

`intake.json` is an array of objects with stable `id`, `from`, `subject`, `body` strings. IDs must use letters, digits, underscores or hyphens. Do not change an ID when retrying the same message. Example:

```json
[{"id":"mail-001","from":"recruiting@example.com","subject":"Interview invitation","body":"Could you share your availability?"}]
```

The worker creates or updates a version-1 backup with classified messages, pending drafts and an activity entry. IDs prevent duplication across repeated runs. Output is replaced atomically with restrictive file permissions. Use **Settings → Restore backup** to load the result; restoration replaces the current browser workspace after review. Back up browser data first. The worker and browser are not a live shared database. Do not run multiple workers on the same output concurrently.

Nothing schedules the worker automatically. To activate recurring processing, choose an OS scheduler and a single writer, provide the intake file from an explicitly authorized source, and retain logs privately. A future service can use a database instead of file snapshots. The current OAuth session is memory-only and is not available to the offline worker.

## Next production steps

- Authenticated persistent service and transactional database with per-user access control.
- Authorized Gmail incremental sync with paging and revoked-token handling.
- Durable, encrypted token storage using a credential store or secret manager.
- Queue with idempotency keys, bounded retries and fresh calendar checks.
- Real model/research adapter with structured output validation, cited sources, freshness timestamps and prompt-injection isolation.
- Source facts tagged as user-provided, imported, inferred or verified; human review for uncertain personal answers.
- Approval records bound to the exact draft, recipient, time and action; edits invalidate approval.
- Delivery adapter only after specific user activation. An approved local draft is never permission for a future service to send it.

Live AI is not implemented or active. When adding it, obtain an explicit credential decision through the secure provider setup, store the key server-side, minimize profile data sent, and document usage costs and retention. The current app does not request or store an AI key.
