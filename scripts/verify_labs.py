"""Real, isolated course acceptance. Never runs learner shell text on the host.

Run: .venv/bin/python scripts/verify_labs.py [--weeks 1 2 3 4 5 6]
Creates only labelled acceptance containers and removes them on completion.
"""
import argparse
import asyncio
import io
import json
import os
import shlex
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aiohttp.test_utils import TestClient, TestServer, unused_port
from server.app import make_app
from server.labs import Labs


async def main(weeks, keep_failed=False):
    state = ROOT / '.state/acceptance-labs'
    state.mkdir(parents=True, exist_ok=True)
    labs = Labs(state)
    course = json.loads((ROOT / 'course/curriculum.json').read_text())
    report = {'started': time.time(), 'weeks': weeks, 'checks': [], 'status': 'running'}
    report_path = ROOT / '.state/acceptance-report.json'
    history = ROOT / '.state/acceptance-history'
    history.mkdir(exist_ok=True)
    if report_path.exists():
        previous = json.loads(report_path.read_text())
        (history / (str(previous['started']) + '.json')).write_text(report_path.read_text())

    def save():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    async def shell(week, script, remote=False, timeout=180):
        name = labs.name(week) + ('-remote' if remote else '')
        proc = await asyncio.create_subprocess_exec(
            'docker', '--context', 'rootless', 'exec', '-u', 'student', '-w', '/workspace',
            name, 'bash', '-c', script, stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            proc.kill(); await proc.wait()
            raise RuntimeError(f'week {week}: shell timed out')
        if proc.returncode:
            raise RuntimeError(f'week {week}: {stdout.decode(errors="replace")[-4000:]}')
        return stdout.decode(errors='replace')

    async def authenticate_peer():
        await shell(4, 'mkdir -p ~/.ssh; chmod 700 ~/.ssh; ssh-keygen -q -t ed25519 -N "" -f ~/.ssh/id_ed25519')
        public = (await shell(4, 'cat ~/.ssh/id_ed25519.pub')).strip()
        await shell(4, 'mkdir -p ~/.ssh; chmod 700 ~/.ssh; printf "%s\\n" ' + shlex.quote(public) + ' > ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys', remote=True)
        _, public = await labs.command('exec', labs.name(4) + '-remote', 'cat', '/etc/ssh/ssh_host_ed25519_key.pub')
        # Trust only the host key read directly from our own labelled SSH peer.
        known = 'workstation ' + ' '.join(public.split()[:2])
        await shell(4, 'printf "%s\\n" ' + shlex.quote(known) + ' > ~/.ssh/known_hosts')

    async def terminal_roundtrip(week):
        port = unused_port()
        async with TestClient(TestServer(make_app(state, port), port=port)) as client:
            token = (await (await client.get('/api/session')).json())['token']
            async with client.ws_connect(f'/api/labs/{week}/terminal', protocols=['linuxlab', token]) as ws:
                await ws.send_json({'type': 'resize', 'rows': 30, 'cols': 100})
                await ws.send_json({'type': 'input', 'data': "printf '\\nPTY_%s_READY\\n' '$((6 * 7))'\r".replace("'$((6 * 7))'", '"$((6 * 7))"')})
                output = b''
                for _ in range(100):
                    msg = await asyncio.wait_for(ws.receive(), 10)
                    if isinstance(msg.data, bytes):
                        output += msg.data
                    if b'PTY_42_READY' in output:
                        return
                raise RuntimeError('PTY output marker missing')

    try:
        health = await labs.health()
        if not health['ready'] or (6 in weeks and not health['modelica_image']):
            raise RuntimeError('Required course images or rootless limits are unavailable: ' + str(health['issues']))
        for week in weeks:
            await labs.reset(week)
            await labs.start(week)
            print(f'week {week}: real container started', flush=True)
            if week == 4:
                await authenticate_peer()
            if week == 1:
                await terminal_roundtrip(week)
                report['terminal_websocket'] = 'passed: PTY, input, resize and real Bash output'
            for lesson in [l for l in course['lessons'] if l['week'] == week]:
                identifier = lesson['id']
                script = lesson['tasks'][0]['solution']
                if identifier == 'w4-3':
                    script = script.replace('# 查看日志，待生成结果后继续', 'for n in {1..100}; do ssh student@workstation "test -s jobs/motor/results/openloop.json" && break; sleep 0.1; done')
                if identifier == 'w6-4':
                    script = script.replace('# 编辑 reports/report.md 填学生姓名与英文摘要', "sed -i 's/学生作者：待填写/学生作者：Automated acceptance fixture/' reports/report.md")
                output = await shell(week, script)
                result = await labs.check(week, identifier)
                report['checks'].append({'lesson': identifier, **result, 'output': output[-6000:]})
                save()
                if result['status'] != 'passed':
                    raise RuntimeError(f'{identifier}: {result}')
                print(identifier + ': passed', flush=True)
                if identifier == 'w3-1':
                    report['science_crosscheck'] = (await shell(week, '.venv/bin/python /opt/course/science_check.py')).strip()
                if identifier == 'w6-2':
                    report['modelica_comparison'] = json.loads(await shell(week, 'cat results/comparison.json'))
            archive = await labs.export(week)
            with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as bundle:
                if './config/motor.json' not in bundle.getnames():
                    raise RuntimeError('Project archive is missing input parameters')
            await labs.stop(week)
            await labs.start(week)
            await shell(week, 'test -f config/motor.json && test -f .course-seeded')
            print(f'week {week}: export and stop/start persistence passed', flush=True)
            await labs.reset(week)
        report['status'] = 'passed'
    except Exception as error:
        report.update(status='failed', error=str(error))
        raise
    finally:
        report['finished'] = time.time()
        save()
        for week in ([] if keep_failed and report['status'] == 'failed' else weeks):
            try:
                await labs.reset(week)
            except Exception as error:
                print(f'Acceptance cleanup week {week}: {error}', file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weeks', type=int, nargs='+', choices=range(1, 7), default=[1, 2, 3, 4, 5])
    parser.add_argument('--keep-failed', action='store_true', help='Keep only acceptance resources for diagnosis after failure')
    args = parser.parse_args()
    asyncio.run(main(args.weeks, args.keep_failed))
