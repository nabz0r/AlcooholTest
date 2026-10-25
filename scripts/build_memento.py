#!/usr/bin/env python3
"""Build immutable public source capsules without fetching external pages."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from catalog.memento import build_capsules, load_research_documents, persist_snapshot, write_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=Path, default=ROOT / 'data/catalog/seed.json')
    parser.add_argument('--research-root', type=Path, default=ROOT / 'data')
    parser.add_argument('--out', type=Path, default=ROOT / 'data/memento')
    parser.add_argument('--assets-root', type=Path, default=ROOT / 'frontend/public')
    parser.add_argument('--zip', type=Path, help='Optional ZIP destination; licensed local files must pass their expected SHA-256.')
    parser.add_argument('--metadata-only', action='store_true', help='Explicitly omit licensed media bytes from the optional ZIP.')
    args = parser.parse_args()
    document = json.loads(args.seed.read_text())
    capsules = build_capsules(document, load_research_documents(args.research_root))
    manifest = persist_snapshot(capsules, args.out)
    bundle = None
    if args.zip:
        args.zip.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.zip.with_name(args.zip.name + '.tmp')
        try:
            bundle = write_bundle(temporary, manifest, args.out, args.assets_root, not args.metadata_only)
            temporary.replace(args.zip)
        finally:
            temporary.unlink(missing_ok=True)
    print(json.dumps({'capsules': manifest['capsules'], 'counts': manifest['counts'],
                      'snapshot_sha256': manifest['snapshot_sha256'], 'original_pages_copied': 0,
                      'index': str(args.out / 'index.json'), 'bundle': {k:v for k,v in bundle.items() if k != 'files'} if bundle else None}, indent=2))


if __name__ == '__main__':
    main()
