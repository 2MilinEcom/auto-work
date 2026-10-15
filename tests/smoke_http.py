"""Run against a locally started server: AW_TEST_ORIGIN=http://localhost:8787 python3 tests/smoke_http.py"""
import http.cookiejar
import json
import os
import urllib.error
import urllib.request

origin = os.environ.get('AW_TEST_ORIGIN', 'http://localhost:8787')
jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def call(path, method='GET', data=None, headers=None):
    request = urllib.request.Request(origin + path, method=method, data=json.dumps(data).encode() if data is not None else None, headers=headers or {})
    try:
        with client.open(request, timeout=5) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers)
assert call('/')[0] == 200
status, body, headers = call('/api/status')
assert status == 200 and 'no-store' in headers['Cache-Control']
csrf = json.loads(body)['csrf']
assert 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Lax' in headers['Set-Cookie']
assert call('/../server.py')[0] == 404
assert call('/.env')[0] == 404
assert call('/api/status', headers={'Host': 'untrusted.example'})[0] == 403
assert call('/api/disconnect', 'POST', {}, {'Origin':'https://untrusted.example','Content-Type':'application/json','X-AW-CSRF':csrf})[0] == 403
assert call('/api/disconnect', 'POST', {}, {'Origin':origin,'Content-Type':'application/json','X-AW-CSRF':'invalid'})[0] == 403
assert call('/oauth/callback?state=invalid&code=fake')[0] == 400
valid = {'Origin':origin,'Content-Type':'application/json','X-AW-CSRF':csrf}
assert call('/api/send', 'POST', {}, valid)[0] == 404
assert call('/api/calendar/create', 'POST', {}, valid)[0] == 404
print('10 HTTP checks passed: app, cookie, no-store, file boundary, Host, Origin, CSRF, OAuth state and absent write routes.')
