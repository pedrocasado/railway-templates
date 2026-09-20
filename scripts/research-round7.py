"""Record round-seven marketplace searches and pinned upstream documentation."""
import concurrent.futures
import datetime
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('research', ROOT / 'scripts/research-round5.py')
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)
research.EVIDENCE = ROOT / '.local/round7/research'
CANDIDATES = {
    'bookwyrm': ('bookwyrm-social/bookwyrm', 'v0.9.3', ['BookWyrm', 'Bookwyrm']),
}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        candidates = dict(pool.map(research.snapshot, CANDIDATES.items()))
    for name, entry in candidates.items():
        print(name, entry['stars'], [(s['query'], s['results']) for s in entry['marketplace']])
    (ROOT / 'sources.round7.lock.json').write_text(json.dumps({
        'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'candidates': candidates,
        'review': {},
    }, indent=2) + '\n')
