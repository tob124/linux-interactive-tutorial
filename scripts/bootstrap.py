"""Install this application's dependencies in its own virtual environment."""
import os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
try:
 subprocess.run([sys.executable,'-m','venv',str(root/'.venv')],check=True)
 subprocess.run([str(root/'.venv/bin/python'),'-m','pip','install','-r',str(root/'requirements.txt')],check=True)
except subprocess.CalledProcessError:
 print('创建环境失败：Ubuntu 用户请先在个人终端安装 python3-venv；网络安装失败可按README使用离线wheels。')
 sys.exit(1)
print('完成。运行 ./start.sh，然后打开 http://127.0.0.1:8765/')
