"""Resolve the round-seven image list without downloading layers."""
import concurrent.futures
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ['ghcr.io/bookwyrm-social/bookwyrm:v0.9.3', 'postgres:17', 'redis:7.4']
path = ROOT / 'images.round7.lock.json'
lock = json.loads(path.read_text()) if path.exists() else {}


def resolve(image):
    if image in lock:
        return image, lock[image]
    digest = subprocess.check_output(['docker', 'buildx', 'imagetools', 'inspect', image, '--format', '{{.Manifest.Digest}}'], text=True).strip()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', digest):
        raise RuntimeError(image + ': invalid registry digest')
    return image, image + '@' + digest


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        lock.update(dict(pool.map(resolve, IMAGES)))
    path.write_text(json.dumps(lock, indent=2, sort_keys=True) + '\n')
    print('Locked', len(lock), 'images')
