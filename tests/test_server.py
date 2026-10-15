import ast
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('aw_server', Path(__file__).resolve().parents[1] / 'server.py')
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class LocalBridgeTests(unittest.TestCase):
    def test_profile_is_allowlisted_and_never_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / 'profile.py'
            profile.write_text("raise RuntimeError('MUST NOT EXECUTE')\nPROFILE = {'first_name':'Alex','last_name':'Example','email':'alex@example.com','school':'Example School','major':'Marketing','preferred_locations':['Example City'],'programming_languages':['Python'],'api_key':'NEVER_IMPORT','gender':'NEVER_IMPORT','phone':'NEVER_IMPORT'}")
            with patch.dict(os.environ, {'RESUME_FILLER_PROFILE': str(profile), 'RESUME_FILLER_RESUME': str(Path(directory) / 'missing.pdf')}):
                result = server.existing_profile()
            self.assertEqual(result['profile']['name'], 'Alex Example')
            self.assertEqual(result['profile']['education'], 'Example School · Marketing')
            self.assertNotIn('NEVER_IMPORT', json.dumps(result))

    def test_tracker_never_treats_uncertain_submission_as_applied(self):
        with tempfile.TemporaryDirectory() as directory:
            tracker = Path(directory) / 'applications.csv'
            tracker.write_text('status,company,title,application_url,notes\nsubmitted,Example A,Intern,https://example.com,Done\nsubmit_uncertain,Example B,Intern,,Check it\nneeds_manual,Example C,Intern,,Manual\n')
            with patch.dict(os.environ, {'RESUME_FILLER_APPLICATIONS': str(tracker)}):
                result = server.existing_applications()['applications']
            self.assertEqual([r['stage'] for r in result], ['Applied', 'Saved', 'Saved'])
            self.assertIn('submit_uncertain', result[1]['notes'])

    def test_missing_profile_has_useful_error(self):
        with patch.dict(os.environ, {'RESUME_FILLER_PROFILE': '/does-not-exist/profile.py'}):
            with self.assertRaisesRegex(ValueError, 'not found'):
                server.existing_profile()

    def test_only_read_scopes_are_requested(self):
        self.assertEqual(len(server.SCOPES), 2)
        self.assertTrue(all(scope.endswith('.readonly') for scope in server.SCOPES))

    def test_plain_text_extraction_ignores_html(self):
        self.assertEqual(server.extract_plain({'mimeType':'text/html','body':{'data':'PHNjcmlwdD5ldmlsPC9zY3JpcHQ+'}}), '')
        self.assertEqual(server.extract_plain({'mimeType':'text/plain','body':{'data':'SGVsbG8'}}), 'Hello')

    def test_token_refresh_never_exposes_refresh_token(self):
        session = {'token': {'access_token':'old','refresh_token':'memory-only','expires_at':0}}
        with patch.object(server, 'request_json', return_value={'access_token':'new','expires_in':3600}):
            self.assertEqual(server.access_token(session), 'new')
        self.assertEqual(session['token']['refresh_token'], 'memory-only')

    def test_expired_token_without_refresh_is_discarded(self):
        session = {'token': {'access_token':'expired','expires_at':0}}
        with self.assertRaisesRegex(ValueError, 'expired'):
            server.access_token(session)
        self.assertNotIn('token', session)


if __name__ == '__main__':
    unittest.main()
