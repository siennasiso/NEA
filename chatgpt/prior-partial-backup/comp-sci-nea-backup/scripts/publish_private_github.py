#!/usr/bin/env python3
"""Publish the verified partial snapshot to a NEW PRIVATE GitHub repository.

Requires Python 3.9+, Git and GitHub CLI authenticated as sisodias.
Dry-run requires only Python and this archive. Never reads or prints tokens.
Uses a separate working copy and never modifies an existing remote repository.
Documentation: https://cli.github.com/manual/gh_repo_create
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from verify_backup import MANIFEST, safe_path, verify

OWNER = 'sisodias'


def run(command: list[str], cwd: Path | None = None, capture: bool = False) -> str:
    result = subprocess.run(command, cwd=cwd, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else ''


def publish(root: Path, name: str, dry_run: bool) -> int:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}', name):
        raise ValueError('Use a repository name of 1–100 letters, numbers, dots, underscores or hyphens, starting with a letter/number.')
    manifest, errors = verify(root)
    if errors:
        raise ValueError('Snapshot verification failed:\n' + '\n'.join(errors))
    target = f'{OWNER}/{name}'
    selected = [item['path'] for item in manifest['files']] + [MANIFEST]
    if dry_run:
        print(f'DRY RUN: Would create a NEW PRIVATE repository: {target}')
        print(f'Would copy and publish exactly {len(selected)} snapshot files, including the manifest.')
        print('Would require GitHub CLI authentication as sisodias; would stop on repository-creation failure.')
        print('No GitHub calls or changes have been made; no local Git repository was created.')
        print('The snapshot remains partial; missing original files and full chats are not retrieved.')
        return 0
    for executable in ('git', 'gh'):
        if shutil.which(executable) is None:
            raise RuntimeError(f'{executable} is not installed. Install it locally, then rerun. This helper installs nothing.')
    run(['gh', 'auth', 'status', '--hostname', 'github.com'])
    login = run(['gh', 'api', '--hostname', 'github.com', 'user', '--jq', '.login'], capture=True)
    if login.lower() != OWNER.lower():
        raise RuntimeError(f'Active GitHub CLI user is {login!r}, not {OWNER!r}; no repository created.')

    work = Path(tempfile.mkdtemp(prefix='comp-sci-nea-github-upload-', dir=str(root.parent)))
    print(f'Local working copy (retained on success or failure): {work}', flush=True)
    for relative in selected:
        source = safe_path(root, relative)
        destination = work / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    run(['git', 'init', '--initial-branch=main'], cwd=work)
    run(['git', 'add', '--', *selected], cwd=work)
    run(['git', '-c', 'user.name=NEA Backup Archive', '-c', 'user.email=nea-backup@example.invalid',
         '-c', 'commit.gpgsign=false', 'commit', '-m',
         'Preserve partial COMP SCI NEA excerpts; original files and full chats not recovered'], cwd=work)

    # --private is explicit. GitHub creation fails rather than overwriting an existing repo.
    # No repository visibility changes, force pushes or credential-file reads are performed.
    print(f'Creating new PRIVATE GitHub repository {target} and pushing this partial snapshot.', flush=True)
    run(['gh', 'repo', 'create', target, '--private', '--source', str(work),
         '--remote', 'origin', '--push', '--description',
         'Partial COMP SCI NEA project archive: visible chat excerpts and recovered notes; originals pending'], cwd=work)

    private = run(['gh', 'repo', 'view', target, '--json', 'isPrivate', '--jq', '.isPrivate'], cwd=work, capture=True)
    if private != 'true':
        raise RuntimeError('Could not verify PRIVATE visibility. Check the repository immediately; upload is not reported as verified.')
    local_sha = run(['git', 'rev-parse', 'HEAD'], cwd=work, capture=True)
    remote_sha = run(['gh', 'api', '--hostname', 'github.com', f'repos/{target}/git/ref/heads/main',
                      '--jq', '.object.sha'], cwd=work, capture=True)
    if local_sha != remote_sha:
        raise RuntimeError('Remote main commit does not match the local snapshot. Upload is not verified.')
    print(f'VERIFIED PRIVATE SNAPSHOT UPLOAD: https://github.com/{target}')
    print(f'Verified commit: {local_sha}')
    print('This is still a PARTIAL backup. Complete conversations and original attachments remain to be recovered.')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='comp-sci-nea-backup', help='New repository name under sisodias.')
    parser.add_argument('--dry-run', action='store_true', help='Verify and preview without GitHub calls or writes.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        return publish(root, args.name, args.dry_run)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'NOT COMPLETED: {exc}', file=sys.stderr)
        print('No successful upload is claimed. A newly created remote may be empty or partial after a push failure.', file=sys.stderr)
        print('Any printed local working directory is retained. Inspect the remote before retrying; do not force-push.', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
