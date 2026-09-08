#!/usr/bin/env python3
"""Verify this partial snapshot; this does not verify full project coverage."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

MANIFEST = 'inventory/file-manifest.json'

def safe_path(root: Path, relative: str) -> Path:
    value = PurePosixPath(relative)
    if value.is_absolute() or not value.parts or any(p in ('..', '.') for p in value.parts) or '\\' in relative:
        raise ValueError(f'Unsafe manifest path: {relative!r}')
    candidate = root.joinpath(*value.parts)
    if candidate.is_symlink() or root not in candidate.resolve().parents:
        raise ValueError(f'Path escapes the snapshot or is a symlink: {relative}')
    return candidate

def verify(root: Path) -> tuple[dict, list[str]]:
    root = root.resolve()
    manifest = json.loads((root / MANIFEST).read_text(encoding='utf-8'))
    errors = []
    seen = set()
    for entry in manifest['files']:
        name = entry['path']
        if name in seen:
            errors.append(f'Duplicate manifest entry: {name}')
            continue
        seen.add(name)
        try:
            path = safe_path(root, name)
            data = path.read_bytes()
            if len(data) != entry['bytes']:
                errors.append(f'Size mismatch: {name}')
            if hashlib.sha256(data).hexdigest() != entry['sha256']:
                errors.append(f'Checksum mismatch: {name}')
        except (OSError, ValueError) as exc:
            errors.append(f'{name}: {exc}')
    if manifest.get('file_count') != len(manifest['files']):
        errors.append('Manifest file count is inconsistent.')
    return manifest, errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        manifest, errors = verify(args.root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Cannot verify snapshot: {exc}', file=sys.stderr)
        return 1
    if errors:
        print('VERIFICATION FAILED\n' + '\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {len(manifest["files"])} snapshot files match their recorded sizes and SHA-256 checksums.')
    print('This checks snapshot integrity only. It does not mean full chats/originals were recovered or anything was uploaded to GitHub.')
    print('Additional files not listed in the manifest are outside this snapshot and will not be uploaded by the included helper.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
