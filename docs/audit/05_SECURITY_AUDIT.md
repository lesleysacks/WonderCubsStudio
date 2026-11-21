# 05 — Security Audit

## 1. Threat model (current)

WonderCubs Studio v0.3 is a single-user, offline desktop application. It makes **no network calls**: a grep for `http`, `requests`, `urllib` and `socket` in `src/` and `app.py` found none. It stores **no credentials**. The attack surface is local: the files it reads (config, images, database) and the files it writes (projects, logs).

The risk profile changes sharply at M5 (AI providers: API keys, outbound HTTPS, untrusted model output) and M6 (publishing: OAuth tokens that can post publicly on a user's behalf). Most recommendations below are **preparatory**.

## 2. Verified good practices

| Practice | Evidence |
|---|---|
| All SQL uses bound parameters; dynamic SQL only interpolates constant column lists | `src/database/*.py` |
| Template rendering is a regex substitution, not `str.format`/Jinja/`eval`, so templates cannot execute code | `prompt_service.py:138–144` |
| No `eval`, `exec`, `pickle`, `subprocess`, `shell=True`, `os.system` | grep (only `os.startfile` found) |
| Project folder names are sanitised, so titles cannot traverse paths (`../`) | `project_service.py:211` |
| User folders are never deleted on failure | `project_service.py:87–89` |
| CI token is read-only | `.github/workflows/tests.yml` `permissions: contents: read` |

## 3. Findings

### S-01 Unpinned dependencies; major-version drift — **High** — Verified
- **Evidence:** `requirements.txt` has `customtkinter>=5.2.2`, which today installs **6.0.0** (plus the unpinned transitive `darkdetect` and `packaging`). `requirements-dev.txt` has `pytest>=8.0,<10`. There is no lock file or hashes.
- **Impact:** Unreviewed code enters every install, a supply-chain exposure. Builds are not reproducible, and the UI may break under a major version it was never tested on (see T-02).
- **Fix:** A pinned lock file with hashes (`pip-compile --generate-hashes` or `uv pip compile`), Dependabot or Renovate for reviewed updates, and `pip-audit` in CI.

### S-02 No secure credential storage design — **Medium (High at M5)** — Verified (absence)
- **Fix before M5:** A `SecretStore` port backed by the OS keychain (Windows Credential Manager, macOS Keychain, Secret Service on Linux), e.g. via `keyring`. That is a justified dependency at M5, not before. Never store keys in `config.json`, SQLite, logs or exports. Redact secrets in logs by default.

### S-03 Logs may capture user content; unbounded size — **Low** — Verified
- **Evidence:** `logger.py` uses `FileHandler` with no rotation. Services log titles, names and folder paths (`main_controller.py:60`, `character_service.py:172`).
- **Fix:** `RotatingFileHandler`, a documented log location, a "clear logs" action, and no prompt or response bodies at INFO once AI arrives.

### S-04 Local data is unencrypted — **Low (accepted)** — Verified
SQLite and project files are plaintext under the user's account. This is normal for desktop creative tools and relies on OS account protection. Document it. Revisit only if encrypted cloud backup is offered, in which case encrypt client-side before upload.

### S-05 GitHub Actions pinned by tag, not SHA — **Low** — Verified
`actions/checkout@v4` and `actions/setup-python@v5`. Pin to commit SHAs once release workflows with signing secrets exist (M8).

### S-06 Untrusted file parsing — **Low** — Verified
`tk.PhotoImage(file=...)` parses user-selected PNGs (`character_preview_panel.py:54`). The risk is low with a maintained Tk. Future media import (M4) should generate thumbnails in a worker process with size and time limits, so a malformed file cannot hang or crash the UI.

### S-07 Future: AI output and prompt injection — **Medium at M5** — Assumption (design-time)
Content pulled into prompts (briefs, research, web text) can contain instructions. Model output written to disk or used as filenames must be treated as untrusted: sanitise names, never auto-execute, and require confirmation before publishing.

### S-08 Future: publishing tokens — **High at M6** — Assumption (design-time)
OAuth tokens with publish scope are the most sensitive asset the product will ever hold. Use OAuth with PKCE through the system browser with a loopback redirect, never embedded webviews collecting passwords. Store tokens in the keychain, request the narrowest scopes, and require explicit per-post confirmation by default.

## 4. Security checks to add to CI (M0.5/M1)
`pip-audit` · `bandit -r src` (advisory) · secret scanning (GitHub native) · dependency review on PRs.
