"""Exercise HTTP boundaries, persistence and the real simulation worker."""
import asyncio
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from aiohttp.test_utils import TestClient, TestServer, unused_port
from server.app import make_app
from server.labs import LabError


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name)
        await self.open_client()

    async def open_client(self):
        self.port = unused_port()
        self.client = TestClient(TestServer(make_app(self.state, self.port), port=self.port))
        await self.client.start_server()
        result = await self.client.get('/api/session')
        self.headers = {'X-Course-Token': (await result.json())['token']}

    async def asyncTearDown(self):
        await self.client.close()
        self.temp.cleanup()

    async def test_origin_host_and_token_boundaries(self):
        self.assertEqual((await self.client.get('/api/progress')).status, 401)
        for extra in ({'Origin': 'https://untrusted.example'},
                      {'Host': 'untrusted.example'}, {'Sec-Fetch-Site': 'cross-site'}):
            result = await self.client.get('/api/session', headers=extra)
            self.assertEqual(result.status, 403)
        result = await self.client.get('/', headers=self.headers)
        self.assertEqual(result.status, 200)
        self.assertIn("frame-ancestors 'none'", result.headers['Content-Security-Policy'])
        self.assertIn('Connor He', await result.text())

    async def test_quiz_is_scored_on_server_and_survives_restart(self):
        course = await (await self.client.get('/api/content/curriculum', headers=self.headers)).json()
        lesson = course['lessons'][0]
        body = {'lesson': lesson['id'], 'read': True, 'answers': [q['answer'] for q in lesson['quiz']], 'checked': True}
        result = await self.client.post('/api/progress', json=body, headers=self.headers)
        row = (await result.json())['lessons'][0]
        self.assertEqual(row['score'], 100)
        self.assertEqual(row['checked'], 0)  # Browser cannot certify its own task.
        self.assertIsNotNone(row['read_at'])
        await self.client.close()
        await self.open_client()
        row = (await (await self.client.get('/api/progress', headers=self.headers)).json())['lessons'][0]
        self.assertEqual(row['score'], 100)

    async def test_invalid_quiz_and_preference_do_not_save_partial_values(self):
        for answers in ([True, 1], [100, 1], [], 'bad'):
            result = await self.client.post('/api/progress', json={'lesson': 'w1-1', 'answers': answers}, headers=self.headers)
            self.assertEqual(result.status, 400)
        result = await self.client.post('/api/preferences', json={'studentName': 'should not save', 'unknown': 1}, headers=self.headers)
        self.assertEqual(result.status, 400)
        data = await (await self.client.get('/api/progress', headers=self.headers)).json()
        self.assertNotIn('studentName', data['preferences'])

    async def test_export_has_separate_authorship_and_no_certification(self):
        await self.client.post('/api/preferences', json={'studentName': 'Test Student', 'reflection': '我的复测记录'}, headers=self.headers)
        text = await (await self.client.get('/api/portfolio/export', headers=self.headers)).text()
        self.assertIn('Connor He 和 Astra', text)
        self.assertIn('学生作者：Test Student', text)
        self.assertIn('未评审', text)
        self.assertEqual((await self.client.get('/api/teacher', headers=self.headers)).status, 200)

    async def test_missing_lab_cannot_mark_completion(self):
        with patch('server.labs.Labs.check', new=AsyncMock(side_effect=LabError('未安装 Docker'))):
            result = await self.client.post('/api/check', json={'lesson': 'w1-1'}, headers=self.headers)
        self.assertEqual(result.status, 409)
        data = await (await self.client.get('/api/progress', headers=self.headers)).json()
        self.assertEqual(data['attempts'], 0)

    async def test_actual_simulation_and_download_agree(self):
        result = await self.client.post('/api/motor/runs', json={'duration': .1}, headers=self.headers)
        self.assertEqual(result.status, 202)
        identifier = (await result.json())['id']
        for _ in range(100):
            status = await (await self.client.get('/api/motor/runs/' + identifier, headers=self.headers)).json()
            if status['status'] != 'running':
                break
            await asyncio.sleep(.02)
        self.assertEqual(status['status'], 'completed')
        self.assertEqual(len(status['result']['series']), 21)
        result = await self.client.get(f'/api/motor/runs/{identifier}/export', headers=self.headers)
        with zipfile.ZipFile(io.BytesIO(await result.read())) as archive:
            self.assertEqual(json.loads(archive.read('experiment.json')), status['result'])
            self.assertEqual(len(archive.read('results.csv').splitlines()), 22)

    async def test_bad_simulation_input_and_unknown_paths(self):
        for body in ({'duration': 100}, {'kp': True}, {'unknown': 1}, []):
            self.assertEqual((await self.client.post('/api/motor/runs', json=body, headers=self.headers)).status, 400)
        self.assertEqual((await self.client.get('/api/motor/runs/not-a-job', headers=self.headers)).status, 400)
        self.assertEqual((await self.client.get('/api/content/secrets', headers=self.headers)).status, 400)

    async def test_restart_marks_interrupted_work(self):
        await self.client.close()
        identifier = 'a' * 32
        folder = self.state / 'runs' / identifier
        folder.mkdir()
        (folder / 'status.json').write_text(json.dumps({'id': identifier, 'status': 'running'}))
        await self.open_client()
        status = await (await self.client.get('/api/motor/runs/' + identifier, headers=self.headers)).json()
        self.assertEqual(status['status'], 'failed')
        self.assertIn('重启', status['error'])
