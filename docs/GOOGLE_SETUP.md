# Hosted Gmail

The hosted dashboard uses the Gmail account you connected to ChatGPT. Open Inbox and click Refresh Gmail. If the service returns reauthentication_required, use the site-generated authorization link and return to refresh. Other errors are shown without claiming the account is disconnected. Only Gmail is declared for the hosted app; Calendar is not yet connected to the website.

The steps below are for the separate downloaded Python app only.

# Activate read-only Google imports

Nothing is connected by default. No Google credential or token is included in this project. The hosted static dashboard cannot call the local Python connector.

1. In your own Google Cloud project, enable Gmail API and Google Calendar API.
2. Configure the OAuth consent screen. For a personal app in testing, add your own Google account as a test user.
3. Create an OAuth client of type **Web application**. Register exactly `http://localhost:8787/oauth/callback` as an authorized redirect URI. If using another port, register that exact URI too.
4. Supply `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to the server environment through your local secret manager or protected shell environment. Do not paste them into the app, source, command history, screenshots or a shared file. The server intentionally does not load `.env` files or read your existing RESUME FILLER credentials.
5. Run `python3 server.py`. Open the local URL, start the personal workspace, go to Settings, and click **Connect Google**. Review Google's consent screen yourself.
6. Click **Sync Gmail** or **Sync calendar**. Sync is on demand; it does not run while closed. Use **Run triage** to classify imported messages, or enable local triage while open.

Requested scopes:

- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/calendar.events.readonly`

The authorization code flow includes state verification and PKCE. Tokens are memory-only and are lost when the local server restarts. The Google client secret never reaches the browser. Both scopes must be granted for this combined connector. No send or write scope is requested.

Gmail imports up to 20 matching messages from the last 30 days using a career keyword query. This is not exhaustive inbox monitoring. IDs prevent duplicates. Only plain-text message bodies or snippets are used; HTML is never executed. Calendar imports up to 250 expanded events on the primary calendar over the next 30 days, including all-day busy blocks. Transparent events do not block availability. A limit warning is returned if pagination remains; conflict checks are limited to the imported data. Other calendars, cancelled events, stale snapshots and external changes can affect availability: sync before deciding.

Disconnect discards this app's in-memory tokens and pending authorization state. It does not delete previously imported data or revoke the provider grant. Clear the personal workspace to remove local data, and use your Google Account's third-party access settings to revoke the app grant if desired.

Google may require additional verification before broad distribution, particularly for Gmail's restricted scopes. This is a local testing foundation. Do not distribute one shared client secret with a packaged app.

Official references checked during implementation:

- [Google web-server OAuth](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Gmail message reads](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get)
- [Calendar event listing](https://developers.google.com/workspace/calendar/api/v3/reference/events/list)
