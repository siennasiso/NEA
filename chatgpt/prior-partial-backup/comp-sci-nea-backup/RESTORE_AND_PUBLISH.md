# Restore and publish this partial snapshot

The backup has NOT been uploaded to GitHub. The intended target is a new PRIVATE repository named `sisodias/comp-sci-nea-backup`.

## Read and verify locally

Extract the ZIP. Open `START_HERE.html` for an offline readable index, or read `README.md`. From the extracted `comp-sci-nea-backup` folder, run:

```bash
python3 scripts/verify_backup.py
```

The checker verifies the original snapshot's file sizes and SHA-256 checksums. It does not prove that all project history was recovered. The file manifest itself is not self-hashed; a separate SHA-256 of the distributed ZIP can validate transport when compared with the separately supplied checksum.

## Create the private GitHub repository

The included helper requires Python 3, Git and an authenticated GitHub CLI (`gh`) on your computer. It does not install software or read tokens from files. Authenticate locally with `gh auth login --hostname github.com` when necessary; never paste a token into a chat or commit one.

First preview without changing GitHub or creating a local repository:

```bash
python3 scripts/publish_private_github.py --dry-run
```

Then run the upload:

```bash
python3 scripts/publish_private_github.py
```

The helper checks that the active GitHub CLI account is `sisodias`, verifies this snapshot, creates a separate sibling working folder, commits only the manifest-listed files, and requests a NEW private repository. It stops if repository creation fails; it does not update an existing repository, force-push, or change your global Git configuration. It checks the repository visibility and remote commit after the push. A success message and link are printed only after those checks pass. The created local working copy is retained for recovery.

The default repository name can be changed to another new name under the same account:

```bash
python3 scripts/publish_private_github.py --name comp-sci-nea-backup-2026-09-07
```

If GitHub created the repository but the push failed, the helper reports the failure and retains the local work directory. Do not assume the remote is complete. Inspect that directory and the repository before retrying a push; this helper deliberately does not overwrite an existing repository.

**Important:** Newly added files that are absent from the original manifest are not published by this helper. Review and commit recovered originals separately. Do not upload a full, unreviewed account export containing unrelated chats.

## Optional Git-history recovery

The separately supplied `.bundle` file contains the committed local archive. It is not proof of a remote upload. Git can restore it to a new folder:

```bash
git clone COMP-SCI-NEA-partial-backup-2026-09-07.bundle nea-backup-restored
```

The ZIP is sufficient for ordinary reading and for the publication helper; the bundle is an additional recovery format.

## Official documentation

GitHub CLI repository creation: <https://cli.github.com/manual/gh_repo_create>.
GitHub CLI authentication: <https://cli.github.com/manual/gh_auth_login>.
Git bundle: <https://git-scm.com/docs/git-bundle>.
ChatGPT account-data export: <https://help.openai.com/en/articles/7260999-how-do-i-export-my-data>.

Repository creation and ChatGPT export instructions were checked against official documentation on 7 September 2026. Account/workspace restrictions may affect export availability. These sources do not imply that this assistant has exported the account or created the remote repository.
