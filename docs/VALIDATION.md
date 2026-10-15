# Validation performed

Build date: October 14, 2026 (America/Los_Angeles).

## Automated checks

- 11 Node engine tests passed: classification precedence, interview detection, idempotent triage, conflict boundaries, buffers, transparent events, invalid dates, alternatives, URL safety, profile validation, personalized brief grounding, ICS escaping/line folding, and workspace separation.
- 7 Python tests passed: safe literal-only profile import without execution, field allowlisting, tracker status mapping, missing profile handling, read-only scopes, HTML exclusion, token refresh, and expired-session cleanup.
- 10 local HTTP smoke checks passed against the running server: successful frontend, session cookie protection, no-store API responses, file access boundary, Host validation, Origin rejection, CSRF rejection, invalid OAuth state, and absent email/calendar write routes.
- Repeated offline-worker run imported one message once and queued one draft once; second run imported zero duplicates.
- Browser JavaScript syntax and Python compilation passed.

## Browser acceptance

Verified in Codex in-app browser at mobile and desktop layouts:

- Overview, navigation and visibly labeled fictional demo.
- Application detail edit/save.
- Manual message import and linked job selection.
- Interview classification with a pending reply draft.
- Repeat triage without extra drafts.
- Overlapping calendar time displays a conflict including the configured buffer.
- Clear alternative creates a reviewable scheduling plan.
- Local scheduling approval workflow and confirmation controls.
- Interview brief, no assumed personal history and explicit template/research status.
- Existing RESUME FILLER profile and optional marketing-resume text loaded locally.
- Profile persists after reload and populates the personal workspace.
- Local existing tracker imported with deduplication; 43 rows yielded 33 unique company/role records on this user's machine. Only explicit submitted statuses map to Applied.

## Limits

Google OAuth and provider reads were implemented from official documentation but not exercised against a live account. No Google credentials were configured. Hosted server integration is not part of the static deployment. AI model calls, automatic company research, email sending, external calendar writes, notifications while closed, and installed recurring jobs are unavailable. Calendar checks are only as complete and fresh as the local/imported events.

The local history is editable browser data, not an immutable security audit. No production multi-user penetration test was performed.

## Hosted Gmail update — October 15, 2026

Added 8 Worker tests for authenticated read routes, origin checks, server-owned bounded queries, isolated request bindings, reauthorization/rate-limit handling, absent writes, message validation, and unconfirmed-result rejection. Total Node tests: 19. Native Gmail get_profile, search_emails and read_email were verified against the connected account. Deployment and browser verification results are reported in the chat. The earlier static-hosting limitation above describes the initial build; the hosted Worker replaces it for Gmail reads only. No model integration or external writes were added.
