---
tags: [git-crypt, git, secrets, bootstrap]
---

# git-crypt

Encrypting the handful of sensitive files in a public dotfiles repo, so the rest of the config can stay public and readable.

## Prerequisites

- `git-crypt` installed — `sudo apt install git-crypt`
- The bootstrap repo cloned, and you can commit to it
- Somewhere to keep the exported key that isn't the repo

## Why it's built this way

The dotfiles repo is public on purpose: the config should be browsable, diffable, and linkable from the docs. A few files in it contain things that shouldn't be — tokens, internal hostnames, machine-specific paths. Only those need protecting.

Options rejected:

- **Making the repo private.** Loses the whole point, and it's one switch away from leaking the day someone flips visibility.
- **A second private repo for the secrets.** Two sources of truth, and the installer has to know about both.
- **Environment variables for everything.** Right answer for tokens, wrong answer for anything that isn't env-shaped — a hostname in a vim config doesn't belong in `$PATH`-adjacent space.
- **SOPS or age.** Heavier, per-file tooling, and every read needs a wrapper. More ceremony than the problem deserves.

git-crypt wins because it's transparent at the git layer: the working tree is plaintext, the repo is ciphertext, and daily use needs no wrapper commands. The only git-crypt-specific action is `unlock` on a fresh machine.

**Symmetric key mode, not GPG.** One key file, works on any machine, no GPG agent to fight. The cost is a single point of failure, which is why step 2 exists.

## Setup

### 1. Arm the repo before the first secret

```bash
cd ~/src/bootstrap
git-crypt init
```

This installs the clean and smudge filters in `.git/config`. It has to happen before the first encrypted file is ever `git add`ed — see the first gotcha.

### 2. Export the key

```bash
git-crypt export-key ~/bootstrap.key
chmod 600 ~/bootstrap.key
```

Not in the repo. Not in a synced folder you don't control. Lose this file and the encrypted content is gone — there is no recovery path in symmetric mode.

### 3. Declare what's encrypted

`.gitattributes` at the repo root:

```
*ssh/config  filter=git-crypt diff=git-crypt
*netrc       filter=git-crypt diff=git-crypt
*.env        filter=git-crypt diff=git-crypt
*vimrc.local filter=git-crypt diff=git-crypt
```

Commit this on its own, before the files it covers.

### 4. Add the files and check the status

```bash
git add .gitattributes configs/vim/_user/.vimrc.local
git-crypt status
```

`.vimrc.local` should be listed as `encrypted`. If it says `not encrypted`, the pattern doesn't match — check with `git check-attr filter -- configs/vim/_user/.vimrc.local`.

### 5. Prove it's ciphertext at rest

Before pushing anything sensitive, confirm what's actually stored:

```bash
git show HEAD:configs/vim/_user/.vimrc.local | head -c 10 | xxd
```

You want:

```
00000000: 0047 4954 4352 5950 5400            .GITCRYPT.
```

If you see your own text, it isn't encrypted. Stop and fix it before the commit leaves the machine.

### 6. Unlock on a fresh machine

```bash
git clone https://github.com/cforqol/bootstrap
cd bootstrap
git-crypt unlock ~/bootstrap.key
```

`setup.sh` does this for you: `app_is_encrypted()` spots the `GITCRYPT` header in the selected app, and `crypto()` prompts for a key path and runs `dots unlock <key>`.

### 7. Skip secrets when you don't have the key

```bash
./setup.sh --all --no-secrets
```

This prunes every app that contains an encrypted file. Note the granularity — see the second gotcha.

## Gotchas

!!! warning
    **Order matters, and history is permanent.** A file committed before its `.gitattributes` pattern exists is stored in plaintext, and adding the pattern later does not encrypt the old blob. If that happened, rotate whatever was in the file — `git filter-repo` only rewrites your copy, not anyone who cloned it.

!!! warning
    **`--no-secrets` is per-app, not per-file.** `app_is_encrypted()` returns true if *any* file under `configs/<app>/` carries the header, and `crypto()` then prunes the whole app. Put an encrypted overlay in its own app directory (`configs/vim-secrets/`) if you want the public half to survive `--no-secrets`.

!!! warning
    **Losing the key means losing the files.** Export it, `chmod 600`, and keep a copy off the machine and off the repo.

- `diff=git-crypt` means `git diff` and `git log -p` show nothing for encrypted files. You can see *that* they changed, never *how*.
- GitHub renders them as binary. File names, sizes, and commit messages stay visible — git-crypt hides content, not structure.
- `git-crypt status -f` re-stages files that were added before the filter matched them.
- `git-crypt lock` refuses to run on a dirty working tree. Commit or stash first.
- One key covers every file in the repo. It is not per-file access control — anyone holding the key gets all of it.
- Don't reuse a key across repos. Rotating means re-keying every clone you have.

## If it breaks

| Symptom | Cause | Fix |
|---------|-------|-----|
| `git-crypt status` says `not encrypted` for a file that should match | `.gitattributes` not committed, pattern wrong, or the file was added before the filter existed | `git check-attr filter -- <path>`, then `git-crypt status -f` |
| `git show HEAD:<file>` prints readable text | Filter never applied — file is plaintext in the repo | Fix the attribute, re-add the file, and treat anything already pushed as leaked |
| `error: external filter 'git-crypt smudge' failed` after clone | Repo has encrypted blobs but no key | `git-crypt unlock ~/bootstrap.key` |
| `Error: Unable to lock, file ... is not committed` | Working tree is dirty | Commit or stash, then `git-crypt lock` |
| `setup.sh --no-secrets` skipped vim entirely | `app_is_encrypted()` is per-app | Move the overlay into its own app dir, e.g. `configs/vim-secrets/` |
| `dots unlock` fails with a key path | Key is for a different repo, or `git-crypt` isn't on `PATH` | Confirm the key decrypts this repo; install `git-crypt` |

## Related

- [Vim setup](vim-setup.md) — the config whose overlay this protects
