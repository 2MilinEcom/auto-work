#!/usr/bin/env python3
"""AUTO WORK local-only server. Python 3.10+. No third-party dependencies.
Google tokens remain in process memory. OAuth and read APIs only; no provider writes.
"""
import ast
import base64
import csv
import hashlib
import http.cookies
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'dist'
PORT = int(os.environ.get('PORT', '8787'))
ORIGIN = f'http://localhost:{PORT}'
REDIRECT = ORIGIN + '/oauth/callback'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/calendar.events.readonly']
SESSIONS = {}
CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')


def request_json(url, data=None, token=None):
    headers = {'Accept': 'application/json'}
    if data is not None:
        data = urllib.parse.urlencode(data).encode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def access_token(session):
    token = session.get('token')
    if not token:
        raise ValueError('Connect Google first.')
    if time.time() >= token.get('expires_at', 0) - 60:
        if not token.get('refresh_token'):
            session.pop('token', None)
            raise ValueError('Google session expired. Connect again.')
        fresh = request_json('https://oauth2.googleapis.com/token', {
            'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token', 'refresh_token': token['refresh_token']})
        token.update(fresh)
        token['expires_at'] = time.time() + fresh.get('expires_in', 3600)
    return token['access_token']


def extract_plain(payload):
    """Never return HTML as active content. Bound imported body size."""
    if payload.get('mimeType') == 'text/plain':
        raw = payload.get('body', {}).get('data', '')
        return base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)).decode('utf-8', 'replace')[:20000]
    for part in payload.get('parts', []):
        value = extract_plain(part)
        if value:
            return value
    return ''


def read_gmail(session):
    token = access_token(session)
    query = urllib.parse.urlencode({'maxResults': 20, 'q': 'newer_than:30d {interview application recruiter internship offer}'})
    listing = request_json('https://gmail.googleapis.com/gmail/v1/users/me/messages?' + query, token=token)
    messages = []
    for item in listing.get('messages', []):
        msg = request_json('https://gmail.googleapis.com/gmail/v1/users/me/messages/' + urllib.parse.quote(item['id'], safe='') + '?format=full', token=token)
        payload = msg.get('payload', {})
        headers = {h['name'].lower(): h['value'] for h in payload.get('headers', [])}
        messages.append({'id': 'gmail-' + msg['id'], 'from': headers.get('from', 'Unknown sender'),
                         'subject': headers.get('subject', '(No subject)'), 'body': extract_plain(payload) or msg.get('snippet', ''),
                         'received': datetime.fromtimestamp(int(msg.get('internalDate', 0)) / 1000, timezone.utc).isoformat(),
                         'category': 'Unprocessed', 'processed': False, 'source': 'google'})
    return {'messages': messages, 'truncated': bool(listing.get('nextPageToken'))}


def read_calendar(session):
    token = access_token(session)
    now = datetime.now(timezone.utc)
    params = urllib.parse.urlencode({'timeMin': now.isoformat(), 'timeMax': (now + timedelta(days=30)).isoformat(),
                                    'singleEvents': 'true', 'orderBy': 'startTime', 'maxResults': 250})
    data = request_json('https://www.googleapis.com/calendar/v3/calendars/primary/events?' + params, token=token)
    events = []
    for event in data.get('items', []):
        if event.get('status') == 'cancelled':
            continue
        start, end = event.get('start', {}), event.get('end', {})
        # All-day events use exclusive end dates; attach the calendar's returned time zone via zoneinfo.
        from zoneinfo import ZoneInfo
        zone = ZoneInfo(data.get('timeZone', 'UTC'))
        def stamp(v):
            if 'dateTime' in v:
                return v['dateTime']
            return datetime.fromisoformat(v['date']).replace(tzinfo=zone).isoformat()
        events.append({'id': 'gcal-' + hashlib.sha256(event['id'].encode()).hexdigest()[:32],
                       'title': event.get('summary', '(Busy)'), 'start': stamp(start), 'end': stamp(end),
                       'type': 'Google Calendar', 'source': 'google', 'busy': event.get('transparency') != 'transparent'})
    return {'events': events, 'truncated': bool(data.get('nextPageToken'))}


def existing_profile():
    """Read only allowlisted literal fields. Never execute the existing project or read its keys."""
    source = Path(os.environ.get('RESUME_FILLER_PROFILE', str(Path.home() / 'Desktop' / 'RESUME FILLER' / 'src' / 'profile.py')))
    if not source.is_file():
        raise ValueError('Existing RESUME FILLER profile not found. Use JSON import, or set RESUME_FILLER_PROFILE to its profile.py path.')
    tree = ast.parse(source.read_text())
    allow = {'first_name', 'last_name', 'email', 'school', 'major', 'expected_graduation', 'city', 'state', 'preferred_locations', 'programming_languages'}
    values = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PROFILE' for t in node.targets) and isinstance(node.value, ast.Dict):
            for k, v in zip(node.value.keys, node.value.values):
                try:
                    key = ast.literal_eval(k)
                    if key in allow:
                        values[key] = ast.literal_eval(v)
                except (ValueError, TypeError, SyntaxError):
                    continue
    if not values:
        raise ValueError('No supported literal profile fields found. Export JSON from your existing app instead.')
    education = ' · '.join(str(values.get(k, '')) for k in ['school', 'major', 'expected_graduation'] if values.get(k))
    location = ', '.join(str(values.get(k, '')) for k in ['city', 'state'] if values.get(k))
    if values.get('preferred_locations'):
        location += ' · Preferred: ' + ', '.join(values['preferred_locations'])
    resume_path = Path(os.environ.get('RESUME_FILLER_RESUME', str(source.parent.parent / 'documents' / 'SampleApplicant_Market_Resume.pdf')))
    experience, skills, about = '', ', '.join(values.get('programming_languages', [])), ''
    if resume_path.is_file():
        try:
            from pypdf import PdfReader
            text = '\n'.join(page.extract_text() or '' for page in PdfReader(str(resume_path)).pages)[:30000]
            if 'Selected Experience' in text:
                experience = text.split('Selected Experience', 1)[1].split('Leadership', 1)[0].strip()
            if '\nSkills' in text:
                skills = text.split('\nSkills', 1)[1].strip()[:2000]
        except ImportError:
            pass  # Optional PDF support. The literal profile import still works.
        except Exception:
            pass  # A damaged PDF must not prevent basic profile loading.
    return {'profile': {'name': ' '.join(str(values.get(k, '')) for k in ['first_name', 'last_name']).strip(),
            'email': values.get('email', ''), 'education': education, 'location': location,
            'skills': skills, 'target': 'Marketing internships',
            'about': about, 'experience': experience, 'fillerURL': ''},
            'source': 'Local RESUME FILLER profile.py; allowlisted literal fields only'}


def existing_applications():
    source = Path(os.environ.get('RESUME_FILLER_APPLICATIONS', str(Path.home() / 'Desktop' / 'RESUME FILLER' / 'applications.csv')))
    if not source.is_file():
        raise ValueError('Existing applications.csv not found. Use JSON import or configure RESUME_FILLER_APPLICATIONS.')
    applications = []
    with source.open(newline='', encoding='utf-8-sig') as stream:
        for index, row in enumerate(csv.DictReader(stream)):
            if index >= 1000:
                break
            if not row.get('company') or not row.get('title'):
                continue
            status = row.get('status', '').lower()
            stage = 'Closed' if any(t in status for t in ['reject', 'closed']) else 'Offer' if 'offer' in status else 'Interview' if 'interview' in status else 'Applied' if status in ['applied', 'submitted', 'success'] else 'Saved'
            applications.append({'company': row['company'][:300], 'role': row['title'][:300],
                'stage': stage, 'description': '', 'url': row.get('application_url') or row.get('handshake_url') or '',
                'notes': ('Imported RESUME FILLER status: ' + row.get('status', '') + '\n' + row.get('notes', ''))[:10000]})
    return {'applications': applications, 'source': 'Local RESUME FILLER applications.csv'}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        # Do not log OAuth authorization codes, cookies, or imported content.
        pass

    def valid_host(self):
        return self.headers.get('Host') == f'localhost:{PORT}'

    def session(self):
        cookie = http.cookies.SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
        except http.cookies.CookieError:
            pass
        sid = cookie.get('aw_session')
        sid = sid.value if sid else None
        session = SESSIONS.get(sid)
        if not session or session['expires'] < time.time():
            sid = secrets.token_urlsafe(32)
            session = {'csrf': secrets.token_urlsafe(32), 'expires': time.time() + 12 * 3600}
            SESSIONS[sid] = session
        self.sid = sid
        return session

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        super().end_headers()

    def json_response(self, data, code=200):
        content = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        if hasattr(self, 'sid'):
            self.send_header('Set-Cookie', f'aw_session={self.sid}; HttpOnly; SameSite=Lax; Path=/; Max-Age=43200')
        self.end_headers()
        self.wfile.write(content)

    def redirect(self, url):
        self.send_response(303)
        self.send_header('Location', url)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

    def do_GET(self):
        if not self.valid_host():
            return self.json_response({'error': f'Open {ORIGIN} using localhost.'}, 403)
        path = urllib.parse.urlsplit(self.path)
        if path.path == '/api/status':
            session = self.session()
            return self.json_response({'local': True, 'configured': bool(CLIENT_ID and CLIENT_SECRET),
                                       'google': bool(session.get('token')), 'profileBridge': True, 'csrf': session['csrf']})
        if path.path == '/oauth/callback':
            session = self.session()
            query = urllib.parse.parse_qs(path.query)
            auth = session.pop('oauth', None)
            if not auth or time.time() - auth['at'] > 600 or not secrets.compare_digest(query.get('state', [''])[0], auth['state']):
                return self.json_response({'error': 'Authorization state expired or mismatched. Connect again from Settings.'}, 400)
            if 'error' in query or 'code' not in query:
                return self.json_response({'error': 'Google access was not granted. Return to the app and try again if desired.'}, 400)
            try:
                token = request_json('https://oauth2.googleapis.com/token', {
                    'code': query['code'][0], 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT, 'grant_type': 'authorization_code', 'code_verifier': auth['verifier']})
                granted = set(token.get('scope', '').split())
                if not set(SCOPES).issubset(granted):
                    return self.json_response({'error': 'Both requested read-only scopes are required for this connector. No token was retained.'}, 400)
                token['expires_at'] = time.time() + token.get('expires_in', 3600)
                session['token'] = token
                return self.redirect('/?google=connected')
            except Exception:
                return self.json_response({'error': 'Google authorization failed. Check OAuth client configuration and try again.'}, 502)
        if path.path.startswith('/api/'):
            return self.json_response({'error': 'Not found'}, 404)
        # Only serve the explicit application assets; no directory listing or secrets.
        if path.path not in ['/', '/index.html', '/app.mjs', '/engine.mjs', '/style.css']:
            return self.json_response({'error': 'Not found'}, 404)
        super().do_GET()

    def do_HEAD(self):
        if not self.valid_host() or urllib.parse.urlsplit(self.path).path not in ['/', '/index.html', '/app.mjs', '/engine.mjs', '/style.css']:
            return self.json_response({'error': 'Not found'}, 404)
        super().do_HEAD()

    def do_POST(self):
        if not self.valid_host() or self.headers.get('Origin') != ORIGIN:
            return self.json_response({'error': 'Same-origin local requests only.'}, 403)
        session = self.session()
        if not secrets.compare_digest(self.headers.get('X-AW-CSRF', ''), session['csrf']):
            return self.json_response({'error': 'Session check failed. Reload the app.'}, 403)
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.json_response({'error': 'JSON required.'}, 415)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or length > 10000:
                return self.json_response({'error': 'Request too large.'}, 413)
            json.loads(self.rfile.read(length) or b'{}')
        except (ValueError, json.JSONDecodeError):
            return self.json_response({'error': 'Invalid JSON.'}, 400)
        path = urllib.parse.urlsplit(self.path).path
        try:
            if path == '/api/resume-filler/applications':
                return self.json_response(existing_applications())
            if path == '/api/resume-filler/profile':
                return self.json_response(existing_profile())
            if path == '/api/oauth/start':
                if not CLIENT_ID or not CLIENT_SECRET:
                    return self.json_response({'error': 'Configure your Google OAuth client in the server environment first.'}, 409)
                verifier = secrets.token_urlsafe(64)
                challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
                state = secrets.token_urlsafe(32)
                session['oauth'] = {'state': state, 'verifier': verifier, 'at': time.time()}
                params = urllib.parse.urlencode({'client_id': CLIENT_ID, 'redirect_uri': REDIRECT, 'response_type': 'code',
                    'scope': ' '.join(SCOPES), 'state': state, 'access_type': 'offline', 'prompt': 'consent',
                    'code_challenge': challenge, 'code_challenge_method': 'S256'})
                return self.json_response({'url': 'https://accounts.google.com/o/oauth2/v2/auth?' + params})
            if path == '/api/sync/gmail':
                return self.json_response(read_gmail(session))
            if path == '/api/sync/calendar':
                return self.json_response(read_calendar(session))
            if path == '/api/disconnect':
                session.pop('token', None)
                session.pop('oauth', None)
                return self.json_response({'disconnected': True})
            return self.json_response({'error': 'This operation is unavailable. No email send or calendar write route exists.'}, 404)
        except ValueError as e:
            return self.json_response({'error': str(e)}, 409)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                session.pop('token', None)
            return self.json_response({'error': f'Google read failed (HTTP {e.code}). Check access and API enablement, then reconnect if needed. No changes were made.'}, 502)
        except Exception:
            return self.json_response({'error': 'Google connection failed. Check your network and OAuth setup. No changes were made.'}, 502)


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'AUTO WORK is ready at {ORIGIN}', flush=True)
    print('Local use only. Press Control+C to stop. Google reads require your own OAuth client.', flush=True)
    server.serve_forever()
