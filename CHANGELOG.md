# Changelog

All notable changes to **NiftyWall** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
