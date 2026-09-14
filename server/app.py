"""Local learning service. Author: Connor He and Astra."""
import argparse
import asyncio
import csv
import fcntl
import io
import json
import os
import pty
import secrets
import shutil
import signal
import sqlite3
import struct
import sys
import termios
import time
import uuid
from pathlib import Path
from aiohttp import web
from .labs import Labs, LabError

ROOT = Path(__file__).resolve().parent.parent


def response(value, status=200):
    return web.Response(text=json.dumps(value, ensure_ascii=False, allow_nan=False), content_type='application/json', status=status)


def make_app(state=None, port=8765):
    state = Path(state or ROOT / '.state')
    state.mkdir(parents=True, exist_ok=True)
    (state / 'runs').mkdir(exist_ok=True)
    token = secrets.token_urlsafe(32)
    hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
    origins = {'http://' + host for host in hosts}
    db = sqlite3.connect(state / 'progress.sqlite3')
    db.row_factory = sqlite3.Row
    db.executescript('''PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS progress(lesson TEXT PRIMARY KEY, read_at REAL, quiz TEXT, score INTEGER DEFAULT 0, checked INTEGER DEFAULT 0, checked_at REAL);
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, lesson TEXT NOT NULL, created REAL NOT NULL, result TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS preferences(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    ''')
    labs = Labs(state)
    processes = {}
    tasks = set()
    run_lock = asyncio.Lock()
    # Interrupted processes cannot survive a service restart as valid jobs.
    for record in (state / 'runs').glob('*/status.json'):
        try:
            status = json.loads(record.read_text())
            if status.get('status') == 'running':
                status.update(status='failed', error='本地服务已重启，请重新运行实验。', finished=time.time())
                record.write_text(json.dumps(status))
        except (OSError, ValueError):
            continue

    @web.middleware
    async def secure(request, handler):
        if request.host not in hosts or request.headers.get('Origin', '') not in origins | {''} or request.headers.get('Sec-Fetch-Site') == 'cross-site':
            return response({'error': '仅允许从本机课程页面访问。'}, 403)
        if request.path.startswith('/api/') and request.path != '/api/session':
            supplied = request.headers.get('X-Course-Token', '')
            if request.path.endswith('/terminal'):
                supplied = request.headers.get('Sec-WebSocket-Protocol', '').split(',')[-1].strip()
            if not secrets.compare_digest(supplied, token):
                return response({'error': '页面会话已过期，请刷新页面。'}, 401)
        try:
            result = await handler(request)
        except (ValueError, KeyError, TypeError) as error:
            result = response({'error': str(error)[:400] or '请求格式不正确。'}, 400)
        except LabError as error:
            result = response({'error': str(error)}, 409)
        result.headers['X-Content-Type-Options'] = 'nosniff'
        result.headers['Referrer-Policy'] = 'no-referrer'
        result.headers['X-Frame-Options'] = 'DENY'
        result.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' ws://127.0.0.1:* ws://localhost:*; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        if request.path.startswith('/api/'):
            result.headers['Cache-Control'] = 'no-store'
        return result

    app = web.Application(middlewares=[secure], client_max_size=65536)

    def curriculum():
        return json.loads((ROOT / 'course/curriculum.json').read_text())

    def lesson(identifier):
        found = next((l for l in curriculum()['lessons'] if l['id'] == identifier), None)
        if not found:
            raise ValueError('未知课程。')
        return found

    async def session(request):
        return response({'token': token, 'version': '1.0', 'authors': ['Connor He', 'Astra']})

    async def content(request):
        name = request.match_info['name']
        if name not in ('curriculum', 'software'):
            raise ValueError('未知内容。')
        return response(json.loads((ROOT / f'course/{name}.json').read_text()))

    async def health(request):
        info = await labs.health()
        info.update({'python': sys.version.split()[0], 'simulation': True, 'disk_free_gb': round(__import__('shutil').disk_usage(state).free / 1024**3, 2)})
        return response(info)

    async def progress(request):
        rows = [dict(r) for r in db.execute('SELECT * FROM progress')]
        for row in rows:
            row['quiz'] = json.loads(row['quiz']) if row['quiz'] else None
        prefs = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM preferences')}
        return response({'lessons': rows, 'preferences': prefs, 'attempts': db.execute('SELECT count(*) FROM attempts').fetchone()[0]})

    async def save_progress(request):
        data = await request.json()
        l = lesson(data['lesson'])
        db.execute('INSERT OR IGNORE INTO progress(lesson) VALUES (?)', (l['id'],))
        if data.get('read') is True:
            db.execute('UPDATE progress SET read_at=? WHERE lesson=?', (time.time(), l['id']))
        if 'answers' in data:
            answers = data['answers']
            if not isinstance(answers, list) or len(answers) != len(l['quiz']) or any(type(a) is not int or not 0 <= a < len(q['options']) for a, q in zip(answers, l['quiz'])):
                raise ValueError('请完成所有理解题。')
            score = round(100 * sum(a == q['answer'] for a, q in zip(answers, l['quiz'])) / len(answers))
            db.execute('UPDATE progress SET quiz=?,score=? WHERE lesson=?', (json.dumps(answers), score, l['id']))
        db.execute('INSERT OR REPLACE INTO preferences(key,value) VALUES (?,?)', ('lastLesson', json.dumps(l['id'])))
        db.commit()
        return await progress(request)

    async def preferences(request):
        data = await request.json()
        allowed = {'studentName', 'projectTitle', 'reflection'}
        if not isinstance(data, dict):
            raise ValueError('作品信息应为对象。')
        for key, value in data.items():
            if key not in allowed or not isinstance(value, str) or len(value) > 5000:
                raise ValueError('作品信息格式不正确。')
        for key, value in data.items():
            db.execute('INSERT OR REPLACE INTO preferences(key,value) VALUES (?,?)', (key, json.dumps(value)))
        db.commit()
        return response({'saved': True})

    async def lab_action(request):
        week = int(request.match_info['week'])
        action = request.match_info['action']
        if action not in ('start', 'stop', 'reset'):
            raise ValueError('未知实验操作。')
        result = await getattr(labs, action)(week)
        if action == 'reset':
            db.execute('UPDATE progress SET checked=0,checked_at=NULL WHERE lesson LIKE ?', (f'w{week}-%',)); db.commit()
        return response(result)

    async def check(request):
        data = await request.json(); l = lesson(data['lesson'])
        result = await labs.check(l['week'], l['id'])
        db.execute('INSERT INTO attempts(lesson,created,result) VALUES (?,?,?)', (l['id'], time.time(), json.dumps(result, ensure_ascii=False)))
        db.execute('INSERT OR IGNORE INTO progress(lesson) VALUES (?)', (l['id'],))
        db.execute('UPDATE progress SET checked=?,checked_at=? WHERE lesson=?', (int(result.get('status') == 'passed'), time.time(), l['id']))
        db.commit()
        return response(result)

    async def export_lab(request):
        week = int(request.match_info['week'])
        data = await labs.export(week)
        return web.Response(body=data, content_type='application/gzip', headers={'Content-Disposition': f'attachment; filename="week-{week}-project.tar.gz"'})

    async def terminal(request):
        week = int(request.match_info['week']); name = labs.name(week)
        if not await labs.exists(name):
            raise LabError('请先启动实验。')
        code, running = await labs.command('inspect', '--format', '{{.State.Running}}', name)
        if code or running.strip() != 'true':
            raise LabError('实验已停止，请重新启动。')
        ws = web.WebSocketResponse(protocols=['linuxlab'], heartbeat=25, max_msg_size=32768)
        await ws.prepare(request)
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
        proc = await asyncio.create_subprocess_exec(*labs.terminal_args(week), stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
        os.close(slave); os.set_blocking(master, False)
        queue = asyncio.Queue(maxsize=64); loop = asyncio.get_running_loop()
        def readable():
            if queue.full():
                loop.remove_reader(master)
                return
            try:
                chunk = os.read(master, 8192)
                if not chunk:
                    loop.remove_reader(master); queue.put_nowait(None); return
                queue.put_nowait(chunk)
            except (OSError, asyncio.QueueFull):
                loop.remove_reader(master)
                if not queue.full(): queue.put_nowait(None)
        loop.add_reader(master, readable)
        async def output():
            while True:
                chunk = await queue.get()
                if chunk is None: break
                await ws.send_bytes(chunk)
                if not ws.closed: loop.add_reader(master, readable)
            await ws.close()
        sender = asyncio.create_task(output())
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get('type') == 'input' and isinstance(data.get('data'), str):
                            encoded = data['data'].encode('utf-8')[:16384]
                            while encoded:
                                try: encoded = encoded[os.write(master, encoded):]
                                except BlockingIOError: await asyncio.sleep(.01)
                        elif data.get('type') == 'resize':
                            rows, cols = int(data['rows']), int(data['cols'])
                            if not 2 <= rows <= 200 or not 10 <= cols <= 400: continue
                            fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
                            os.killpg(proc.pid, signal.SIGWINCH)
                    except (ValueError, KeyError, OSError):
                        await ws.close(code=1008, message=b'Invalid terminal message')
        finally:
            loop.remove_reader(master); sender.cancel(); os.close(master)
            await asyncio.gather(sender, return_exceptions=True)
            if proc.returncode is None:
                proc.terminate()
                try: await asyncio.wait_for(proc.wait(), 3)
                except asyncio.TimeoutError: proc.kill(); await proc.wait()
        return ws

    async def run_motor(request):
        from .motor import validate_config
        config = validate_config(await request.json())
        async with run_lock:
            if len(processes) >= 2:
                return response({'error': '已有实验正在计算，请等待或停止。'}, 429)
            # Retain at most 30 jobs, including active jobs; never prune active work.
            folders = sorted((state / 'runs').iterdir(), key=lambda p: p.stat().st_mtime)
            for old in [p for p in folders if p.is_dir() and p.name not in processes][:max(0, len(folders) - 29)]:
                shutil.rmtree(old)
            identifier = uuid.uuid4().hex
            folder = state / 'runs' / identifier; folder.mkdir()
            (folder / 'config.json').write_text(json.dumps(config, ensure_ascii=False))
            status = {'id': identifier, 'status': 'running', 'started': time.time()}
            (folder / 'status.json').write_text(json.dumps(status))
            try:
                proc = await asyncio.create_subprocess_exec(sys.executable, '-m', 'server.simworker', str(folder), cwd=ROOT, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
            except OSError:
                status.update(status='failed', error='无法启动计算进程，请检查本机资源。')
                (folder / 'status.json').write_text(json.dumps(status))
                return response(status, 503)
            processes[identifier] = proc
        async def finish():
            try:
                _, stderr = await asyncio.wait_for(proc.communicate(), 30)
                status['status'] = 'completed' if proc.returncode == 0 else 'failed'
                if proc.returncode: status['error'] = '数值求解未完成，请检查参数或重新运行。'
            except asyncio.TimeoutError:
                proc.kill(); await proc.wait(); status.update(status='failed', error='计算超时，已停止。')
            finally:
                if (folder / 'cancelled').exists(): status['status'] = 'cancelled'
                status['finished'] = time.time()
                (folder / 'status.json').write_text(json.dumps(status))
                processes.pop(identifier, None)
        task = asyncio.create_task(finish()); tasks.add(task); task.add_done_callback(tasks.discard)
        return response(status, 202)

    def run_folder(identifier):
        if len(identifier) != 32 or any(c not in '0123456789abcdef' for c in identifier):
            raise ValueError('未知运行编号。')
        folder = state / 'runs' / identifier
        if not (folder / 'status.json').exists(): raise ValueError('运行记录不存在。')
        return folder

    async def motor_result(request):
        folder = run_folder(request.match_info['id'])
        status = json.loads((folder / 'status.json').read_text())
        if status['status'] == 'completed': status['result'] = json.loads((folder / 'result.json').read_text())
        return response(status)

    async def cancel_motor(request):
        identifier = request.match_info['id']; folder = run_folder(identifier)
        proc = processes.get(identifier)
        if proc and proc.returncode is None:
            (folder / 'cancelled').touch()
            try: proc.terminate()
            except ProcessLookupError: pass
        return response({'status': 'cancelling'})

    async def motor_export(request):
        folder = run_folder(request.match_info['id'])
        if json.loads((folder / 'status.json').read_text())['status'] != 'completed' or not (folder / 'result.json').exists():
            raise ValueError('该实验还没有可导出的结果。')
        import zipfile
        result = json.loads((folder / 'result.json').read_text())
        buffer = io.BytesIO(); output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(result['series'][0])); writer.writeheader(); writer.writerows(result['series'])
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('results.csv', output.getvalue()); z.writestr('experiment.json', json.dumps(result, ensure_ascii=False, indent=2)); z.writestr('README.txt', '课程作者：Connor He 和 Astra\n学生作者：请填写\n这是教学电机平均模型的数值结果，不是实测数据。\n所有参数、单位、模型和求解设置见 experiment.json。\n')
        return web.Response(body=buffer.getvalue(), content_type='application/zip')

    async def portfolio_export(request):
        data = json.loads((await progress(request)).text)
        prefs = data['preferences']; rows = data['lessons']
        text = f"# Linux 工程实践学习记录\n\n课程作者：Connor He 和 Astra\n\n学生作者：{prefs.get('studentName', '未填写')}\n\n项目：{prefs.get('projectTitle', '虚拟电机调试')}\n\n"
        text += '## 学习证据\n\n| 单元 | 已阅读 | 理解题 | 实验检查 |\n|---|---|---|---|\n'
        for r in rows: text += f"| {r['lesson']} | {'是' if r['read_at'] else '否'} | {r['score']}% | {'通过' if r['checked'] else '未通过/未检查'} |\n"
        text += '\n## 项目复盘\n\n' + prefs.get('reflection', '尚未填写') + '\n\n## 人工评审\n\n状态：未评审。自动检查与学生自评不代表教师认证。\n\n正确性40%、复现性25%、排障20%、表达15%。\n'
        return web.Response(text=text, content_type='text/markdown')

    async def teacher(request):
        return web.FileResponse(ROOT / 'docs/TEACHER.md')

    async def index(request):
        return web.FileResponse(ROOT / 'dist/index.html')

    async def cleanup(app):
        for proc in list(processes.values()):
            if proc.returncode is None: proc.terminate()
        await asyncio.gather(*tasks, return_exceptions=True)
        db.close()

    app.on_cleanup.append(cleanup)
    app.router.add_get('/api/session', session)
    app.router.add_get('/api/content/{name}', content)
    app.router.add_get('/api/health', health)
    app.router.add_get('/api/progress', progress)
    app.router.add_post('/api/progress', save_progress)
    app.router.add_post('/api/preferences', preferences)
    app.router.add_post('/api/check', check)
    app.router.add_post('/api/labs/{week}/{action}', lab_action)
    app.router.add_get('/api/labs/{week}/terminal', terminal)
    app.router.add_get('/api/labs/{week}/export', export_lab)
    app.router.add_post('/api/motor/runs', run_motor)
    app.router.add_get('/api/motor/runs/{id}', motor_result)
    app.router.add_post('/api/motor/runs/{id}/cancel', cancel_motor)
    app.router.add_get('/api/motor/runs/{id}/export', motor_export)
    app.router.add_get('/api/portfolio/export', portfolio_export)
    app.router.add_get('/api/teacher', teacher)
    app.router.add_get('/', index)
    app.router.add_static('/', ROOT / 'dist', show_index=False, follow_symlinks=False)
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--port', type=int, default=8765); parser.add_argument('--state'); args = parser.parse_args()
    web.run_app(make_app(args.state, args.port), host='127.0.0.1', port=args.port, access_log=None)
