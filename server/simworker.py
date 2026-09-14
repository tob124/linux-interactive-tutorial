import json
import sys
from pathlib import Path
from .motor import simulate

if __name__ == '__main__':
    folder = Path(sys.argv[1])
    result = simulate(json.loads((folder / 'config.json').read_text()))
    (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False, allow_nan=False))
