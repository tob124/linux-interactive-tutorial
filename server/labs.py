"""Own only labelled course containers. Never execute student text on the host."""
import asyncio
import hashlib
import json
import os
import shutil
from pathlib import Path

IMAGE = 'mechlinux-base:1.0'
MODELICA_IMAGE = 'mechlinux-modelica:1.0'


class LabError(Exception):
    pass


class Labs:
    def __init__(self, state: Path):
        self.prefix = 'mechlinux-' + hashlib.sha256(str(state.resolve()).encode()).hexdigest()[:10]
        self.lock = asyncio.Lock()

    def name(self, week):
        if type(week) is not int or not 1 <= week <= 6:
            raise LabError('项目编号必须为 1–6。')
        return f'{self.prefix}-w{week}'

    async def command(self, *args, timeout=15, limit=1048576):
        if not shutil.which('docker'):
            raise LabError('未找到 Docker。请先完成“软件与环境”中的本机准备。')
        proc = await asyncio.create_subprocess_exec('docker', '--context', 'rootless', *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out = bytearray()
        async def read():
            while chunk := await proc.stdout.read(8192):
                out.extend(chunk)
                if len(out) > limit:
                    raise LabError('命令输出超过课堂限制，已停止。')
            await proc.wait()
        try:
            await asyncio.wait_for(read(), timeout)
        except (asyncio.TimeoutError, LabError):
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
            raise LabError('实验操作超时或输出过多，请检查实验状态。')
        return proc.returncode, out.decode('utf-8', 'replace')

    async def health(self):
        info = {'docker': bool(shutil.which('docker')), 'rootless': False, 'limits': False, 'image': False, 'modelica_image': False, 'ready': False, 'issues': [], 'sessions': []}
        if not info['docker']:
            info['issues'].append('Docker 尚未安装；课程阅读与网页电机计算仍可使用。')
            return info
        try:
            code, raw = await self.command('info', '--format', '{{json .}}', timeout=8)
            if code:
                info['issues'].append('Docker 服务不可用，请在本机启动 rootless Docker。')
                return info
            meta = json.loads(raw)
            info['rootless'] = any('rootless' in x for x in meta.get('SecurityOptions', []))
            info['limits'] = str(meta.get('CgroupVersion')) == '2' and bool(meta.get('MemoryLimit')) and bool(meta.get('PidsLimit'))
            if not info['rootless']:
                info['issues'].append('当前 Docker 并非 rootless 模式；课程不会自动改用宿主机高权限执行。')
            if not info['limits']:
                info['issues'].append('未确认 cgroup v2 内存及进程限制可用，请检查用户服务与控制器委派。')
            for key, image in [('image', IMAGE), ('modelica_image', MODELICA_IMAGE)]:
                code, _ = await self.command('image', 'inspect', image)
                info[key] = code == 0
            if not info['image']:
                info['issues'].append('基础实验镜像未准备。请在本机运行 ./scripts/prepare-labs.sh。')
            info['ready'] = info['rootless'] and info['limits'] and info['image']
            _, raw = await self.command('ps', '-a', '--filter', f'label=org.mechlinux.owner={self.prefix}', '--format', '{{json .}}')
            info['sessions'] = [json.loads(x) for x in raw.splitlines() if x.startswith('{')]
        except (LabError, ValueError):
            info['issues'].append('无法读取 Docker 状态，请检查本机环境。')
        return info

    async def exists(self, name):
        code, data = await self.command('inspect', '--format', '{{json .Config.Labels}}', name)
        if code:
            return False
        if json.loads(data).get('org.mechlinux.owner') != self.prefix:
            raise LabError('发现同名但不属于本课程的资源，已停止操作。')
        return True

    async def start(self, week):
        name = self.name(week)
        async with self.lock:
            health = await self.health()
            if not health['ready']:
                raise LabError('；'.join(health['issues']))
            if week == 6 and not health['modelica_image']:
                raise LabError('第 6 周需要 OpenModelica 软件包缓存。请运行 ./scripts/prepare-labs.sh --modelica。')
            for session in health['sessions']:
                other = session.get('Names', '')
                if other not in (name, name + '-remote') and other.startswith(self.prefix):
                    await self.command('stop', '--time', '3', other)
            network = name + '-net'
            if week == 4:
                code, labels = await self.command('network', 'inspect', '--format', '{{json .Labels}}', network)
                if not code and (json.loads(labels) or {}).get('org.mechlinux.owner') != self.prefix:
                    raise LabError('发现不属于本课程的同名网络，已停止操作。')
                if code:
                    code, text = await self.command('network', 'create', '--internal', '--label', f'org.mechlinux.owner={self.prefix}', network)
                    if code:
                        raise LabError(text[:500])
                await self._create(name + '-remote', IMAGE, week, network, remote=True)
            await self._create(name, MODELICA_IMAGE if week == 6 else IMAGE, week, network if week == 4 else 'none')
            result = {'week': week, 'status': 'running', 'message': '实验已启动。工作文件会保留；切换项目会停止上一项目中的进程。'}
            if week == 4:
                code, fingerprint = await self.command('exec', name + '-remote', 'ssh-keygen', '-lf', '/etc/ssh/ssh_host_ed25519_key.pub')
                result['fingerprint'] = fingerprint.strip() if code == 0 else ''
            return result

    async def _create(self, name, image, week, network, remote=False):
        if await self.exists(name):
            code, out = await self.command('start', name)
        else:
            args = ['run', '-d', '--name', name, '--label', f'org.mechlinux.owner={self.prefix}', '--hostname', 'workstation' if remote else f'lab-w{week}', '--network', network, '--memory', '192m' if remote else '768m', '--cpus', '1', '--pids-limit', '128', '--cap-drop', 'NET_RAW', '--mount', f'type=volume,src={name}-work,dst=/workspace', '--mount', f'type=volume,src={name}-home,dst=/home/student', '-e', f'COURSE_WEEK={week}']
            if remote:
                args += ['--network-alias', 'workstation']
            if week not in (1, 6) and not remote:
                args += ['--security-opt', 'no-new-privileges=true']
            args += [image, 'remote' if remote else 'lab']
            code, out = await self.command(*args, timeout=45)
        if code:
            raise LabError(out[-800:])
        for _ in range(30):
            code, _ = await self.command('exec', name, 'test', '-f', '/tmp/course-ready')
            if code == 0:
                break
            await asyncio.sleep(.2)
        else:
            raise LabError('实验初始化失败。请检查镜像；已有文件已保留。')
        code, value = await self.command('exec', name, 'cat', '/sys/fs/cgroup/memory.max')
        if code or value.strip() == 'max':
            await self.command('stop', name)
            raise LabError('实验内存限额未生效，已停止实验。')

    async def check(self, week, lesson):
        name = self.name(week)
        if not await self.exists(name):
            raise LabError('请先启动这一周的实验环境。')
        code, raw = await self.command('exec', '-u', 'student', '-w', '/workspace', name, 'python3', '/opt/course/checks.py', lesson, timeout=50)
        try:
            result = json.loads(raw)
        except ValueError:
            raise LabError('检查器未能运行。请确认实验正在运行，并检查所需软件。')
        return result

    def terminal_args(self, week):
        return ['docker', '--context', 'rootless', 'exec', '-it', '-u', 'student', '-w', '/workspace', '-e', 'TERM=xterm-256color', self.name(week), 'tmux', 'new-session', '-A', '-s', 'course', 'bash', '-l']

    async def stop(self, week):
        async with self.lock:
            name = self.name(week)
            for n in (name, name + '-remote'):
                if await self.exists(n):
                    await self.command('stop', '--time', '3', n)
            return {'status': 'stopped', 'message': '文件已保留；运行中的进程已停止。'}

    async def reset(self, week):
        async with self.lock:
            name = self.name(week)
            for n in (name, name + '-remote'):
                if await self.exists(n):
                    await self.command('rm', '-f', n)
                    for suffix in ('-work', '-home'):
                        await self.command('volume', 'rm', n + suffix)
            if week == 4:
                code, data = await self.command('network', 'inspect', '--format', '{{json .Labels}}', name + '-net')
                if not code and json.loads(data).get('org.mechlinux.owner') == self.prefix:
                    await self.command('network', 'rm', name + '-net')
            return {'status': 'reset', 'message': '当前项目实验已重置。历史尝试保留，本轮任务需重新检查。'}

    async def export(self, week):
        name = self.name(week)
        if not await self.exists(name):
            raise LabError('该项目尚无可导出的实验环境。')
        proc = await asyncio.create_subprocess_exec('docker', '--context', 'rootless', 'exec', '-u', 'student', name, 'tar', '--exclude=.venv', '--exclude=build', '--exclude=*.tar.gz', '-czf', '-', '-C', '/workspace', '.', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        data = bytearray()
        async def read():
            while chunk := await proc.stdout.read(65536):
                data.extend(chunk)
                if len(data) > 20 * 1024 * 1024:
                    raise LabError('导出文件超过 20 MB，请先整理大型结果文件。')
            await proc.wait()
        try:
            await asyncio.wait_for(read(), 30)
        except (asyncio.TimeoutError, LabError) as error:
            if proc.returncode is None: proc.kill()
            await proc.wait()
            raise LabError(str(error) or '导出超时，请减少实验目录中的大型文件。')
        if proc.returncode:
            raise LabError('导出失败。请确认实验正在运行，且当前没有程序修改结果文件。')
        return bytes(data)
