#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export DOCKER_CONTEXT=rootless
command -v docker >/dev/null || { echo '请先按官方说明安装 rootless Docker。'; exit 1; }
docker info --format '{{json .SecurityOptions}}' | grep -q rootless || { echo '需要 rootless Docker。'; exit 1; }
test "$(docker info --format '{{.CgroupVersion}}')" = 2 || { echo '需要cgroup v2资源限制。'; exit 1; }
python3 - <<'PY'
import shutil,sys
free=shutil.disk_usage('.').free/1024**3
print(f'当前项目所在磁盘可用 {free:.1f} GiB；还需检查 Docker 数据目录所在磁盘。')
if free<4:sys.exit('请预留至少4GiB用于基础镜像下载、解包与构建。OpenModelica建议额外预留4GiB。')
PY
docker build -f lab/Dockerfile -t mechlinux-base:1.0 .
mkdir -p .state
docker image inspect mechlinux-base:1.0 > .state/base-image-manifest.json
if [ "${1:-}" = --modelica ]; then
  docker build -f lab/Dockerfile.modelica -t mechlinux-modelica:1.0 .
  docker image inspect mechlinux-modelica:1.0 > .state/modelica-image-manifest.json
fi
echo '镜像准备完成。回到网页重新检查环境。'
