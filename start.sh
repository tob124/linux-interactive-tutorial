#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c 'import aiohttp' 2>/dev/null; then
  echo '请先运行：python3 scripts/bootstrap.py'; exit 1
fi
export DOCKER_CONTEXT=rootless
exec .venv/bin/python -m server.app "$@"
