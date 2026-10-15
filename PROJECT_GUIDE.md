# AUTO WORK — your career, in motion

A runnable personal career dashboard for Sample's UC Berkeley / marketing internship workflow. The source contains no personal contact details, resume contents, credentials, tokens, or real emails. It starts in the personal workspace. Fictional examples are available only through Explore demo. Your actual profile can be loaded locally from your existing RESUME FILLER project.

## Run in two steps

1. Unzip the download and open a terminal in the `auto-work` folder.
2. Run:

```sh
python3 server.py
```

Open **http://localhost:8787**. Python 3.10+ is required. No package installation or build is needed. If port 8787 is occupied, use `PORT=8793 python3 server.py` and open http://localhost:8793. On Windows PowerShell, set `$env:PORT="8793"` before running.

The app's local server binds only to this computer. Keep the terminal open; Control+C stops it. Prefer `localhost`, not `127.0.0.1`, because Host and Origin checks use localhost.

## Start with your actual profile

Click **Start my workspace → About me → Load RESUME FILLER profile**. The local bridge reads the literal `PROFILE` dictionary at `~/Desktop/RESUME FILLER/src/profile.py`. It does not import or execute that project, reuse its API keys, or change any of its files. It imports only name, email, education, city, preferred locations, and programming skills. Sensitive demographic and authorization fields are excluded.

Optional: to also import the **Selected Experience** and **Skills** sections from your existing marketing resume, install the optional PDF reader before starting the server:

```sh
python3 -m pip install -r requirements-optional.txt
```

The default resume path is `~/Desktop/RESUME FILLER/documents/SampleApplicant_Market_Resume.pdf`. For different paths set `RESUME_FILLER_PROFILE` and/or `RESUME_FILLER_RESUME` in your environment. Paths remain on the server. Review imported facts: the resume and profile may disagree about details such as graduation month. No source is independently verified.

In Applications, **Load existing tracker** reads your local `applications.csv` and lets you import records. Only explicitly submitted records become Applied; uncertain submissions stay Saved with the original status in notes.

You can also import a JSON profile, or edit your details manually. Save your short introduction, real experience, skills and goals. **Never paste API keys into profile fields.** Profile changes update interview preparation and newly created reply drafts. Existing drafts keep their wording until you edit them.

## What works now

- Responsive dashboard, with separate fictional demo and real personal workspaces.
- Saved personal profile; safe local read bridge to existing RESUME FILLER facts and optional resume text.
- Inbox import, search, category correction, job linking and transparent keyword triage.
- Interview detection that queues a local reply draft, with duplicate prevention.
- Application tracker with stages, descriptions, job links, follow-up dates and notes.
- Calendar blocks, overlap checks with configurable buffers, alternate-time suggestions and manual `.ics` export.
- Scheduling plans and reply drafts requiring local review; approved schedules add a local hold and future 24-hour / 1-hour in-app prep reminders. No external actions on approval.
- Personal preparation from your saved facts and the job description; sourced company-note workspace distinguishing facts from hypotheses; practice questions, notes and downloadable briefs.
- Reminders with completion and snooze; in-app alerts while open.
- Local activity history, profile export, application import, backup and restore.
- Optional real Google OAuth connector for on-demand, **read-only** Gmail and primary Calendar imports. See `docs/GOOGLE_SETUP.md`.
- Idempotent offline worker that can be scheduled explicitly. See `docs/AUTOMATION.md`.

## What is not activated

- No OpenAI or other model API calls. Triage and preparation are deterministic rules/templates, clearly labeled in the app.
- No automatic web research or independently verified company facts. You add sources and notes.
- No email sending, application submission, or external calendar changes; these endpoints do not exist.
- No background process or recurring task installed on your computer. Browser automations stop when closed.
- No desktop, email or push notifications.
- No direct update of your Chrome extension's saved profile. Export/import is a contract, not a claimed extension connection.
- Local Python OAuth remains untested against a live account; hosted Gmail is a separate connected-app path.

The hosted private version now supports live Gmail reads through your connected ChatGPT Gmail account. In Inbox, click Refresh Gmail to load up to 20 recent matching messages. Open a message and use Read full email to retrieve its plain-text body. Settings shows the verified connected account or the exact connection error. You may need to authorize Gmail for this site through its ChatGPT sign-in flow. No Google Cloud client is needed for hosted Gmail. **The Python OAuth connector and local filesystem bridge still work only in the downloaded local app.** Data at the hosted URL, localhost, and different ports are separate because browser storage is origin-specific. Back up and restore to move between them.

## Data and credentials

App data is in browser local storage; it persists across reloads but is **not encrypted**. Use a private device. There is no telemetry or analytics. Google Fonts is the only external visual resource and gracefully falls back to system fonts offline. The published code includes no personal profile or email payload. Gmail data is fetched per signed-in request and saved only in the current browser workspace. The connected account name/email initialize an otherwise empty profile.

Google OAuth client credentials come from server environment variables only; no secrets are included in code. Access and refresh tokens stay in process memory, never in browser storage, logs, ZIPs or source files. Disconnect or restart to discard them. Google account access can also be revoked in Google's account settings. No AI API key is requested or stored. If AI is enabled later, use an OS credential store or hosting secret manager and server-only calls; never put keys in local storage or frontend bundles.

The local server validates Host, Origin and a per-session CSRF token on POST, uses HttpOnly/SameSite cookies, checks OAuth state and PKCE, serves only five allowlisted app assets, and suppresses request logs. This is a personal local foundation, not a hardened multi-user server. Do not expose it on a network or place a reverse proxy in front of it without adding production authentication, HTTPS, persistent encrypted storage, rate limiting and independent security review.

## Test

Node 20+ is needed for the offline worker and engine tests, not for running the dashboard.

```sh
node --test tests/engine.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

Manual acceptance: add a profile; add a job; import an interview invitation; run triage twice; review the draft; add a busy block; propose an overlapping time; verify a conflict; propose a free time; approve and export the plan; add a source and export a brief; reload and verify persistence. See `docs/VALIDATION.md` for checks performed during this build.

## Structure

- `dist/`: complete frontend; no build step.
- `dist/engine.mjs`: shared classification, scheduling, profile, brief and export logic.
- `server.py`: local static server, profile bridge and read-only Google OAuth/API adapter.
- `worker.mjs`: offline JSON intake worker.
- `tests/`: meaningful engine and server regression checks.
- `docs/`: Google activation, automation, RESUME FILLER contract and extension roadmap.

All synced ChatGPT project source files were left unchanged.

## Hosted Gmail implementation

`worker/handler.mjs` is a small Worker server using the bundled Sites request-scoped connector contract. Its server-owned routes invoke only Gmail get_profile, search_emails (fixed query, max 20), and read_email (validated message ID). Authentication, same-origin JSON POSTs and private/no-store responses are enforced. Site declarations request read_only access. No provider token enters the browser or source tree. `node scripts/build-hosted.mjs` embeds the frontend assets into dist/server/index.js and copies the hosting manifest. The build has no dependencies. Source assets remain in dist/ for compatibility with the local Python server.
