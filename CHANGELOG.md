# Changelog

All notable changes to **NiftyWall** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.4.0] - 2026-07-01

### Security
- Added authentication to all `/api/panic/*` endpoints (freeze, resume, toggle, status, processes).
- Added authentication to `/api/whois/{ip}` endpoint with IP validation (SSRF protection).
- Replaced `dict` body parameters with strict Pydantic models in `/api/fail2ban/*` endpoints.
- Fixed `get_db` import in `settings_router.py` (was incorrectly imported from `auth` instead of `db`).
- Validated panic mode interface names from environment variables to prevent nftables injection.
- Fixed broken rate-limit exception handler (`r.status_code(429)` → proper `JSONResponse`).

### Changed
- Upgraded `requests` to 2.34.2, `fastapi` to 0.115.12, `psutil` to 7.0.0, `gunicorn` to 23.0.0, `bcrypt` to 4.3.0, `uvicorn` to 0.34.3.
- Replaced deprecated `@app.on_event("startup")` with FastAPI `lifespan` context manager.
- Dynamic version reading from `VERSION` file in `main.py`.
- Added explicit `permissions: contents: read` to CI workflow (fixes CodeQL alert).

### Fixed
- Removed duplicate `datetime` import in `auth.py`.
- Removed committed `audit.log` from repository.
- Synchronized version across `VERSION`, `pyproject.toml`, and `Dockerfile`.

---

## [3.3.0] - 2026-06-30

### Added
- **`.env.example`** — Template environment file with documented variables for SECRET_KEY, PANIC_ALLOWED_PORTS, PANIC_ALLOWED_INTERFACES, and optional integrations.
- **`docker-compose.yml.example`** — Hardened Docker Compose configuration using minimal capabilities (`NET_ADMIN`, `NET_RAW`, `SYS_ADMIN`) instead of full privileged mode, with healthcheck, Traefik labels, and named volumes.
- **Issue templates** — `bug_report.md` and `feature_request.md` in `.github/ISSUE_TEMPLATE/` for standardized issue reporting.
- **PR template** — `PULL_REQUEST_TEMPLATE.md` with checklist for bug fixes, features, security, and testing.
- **`SECURITY.md`** — Security policy with vulnerability reporting guidelines.

### Changed
- README.md now includes Docker security best practices and full architecture diagram.
- Project branding aligned across README, badges, and documentation.

### Fixed
- Docker Compose example no longer requires `privileged: true` — uses capability-based security model.
- Healthcheck uses Python urllib instead of curl for slim image compatibility.

### Security
- Replaced `privileged: true` with `cap_drop: [ALL]` + selective `cap_add` for defense in depth.
- Added `security_opt: no-new-privileges:true` to prevent privilege escalation.
- `.env` and `data/` explicitly excluded from version control via `.gitignore`.
- All user input validated through Pydantic models to prevent nftables injection.

---

## [3.2.3] - Previous Release

### Added
- Initial Hardened edition with SQLite backend.
- Strict input validation via Pydantic.
- Isolated Time Machine for snapshot management.
- Smart DNAT + SNAT for asymmetric routing.
- Resilient Fail2Ban integration via `fail2ban-client`.

### Changed
- Full migration from JSON storage to SQLite database.
- Race condition fixes in user state management.

---

## [3.0.0] - Hardened Edition

### Added
- Complete security audit and hardening.
- Enterprise-grade state persistence with SQLite.
- SAFE Mode and Panic Mode features.
- Docker-hosted deployment with host networking.

---

*For the full version history, see [GitHub Releases](https://github.com/weby-homelab/niftywall/releases).*
