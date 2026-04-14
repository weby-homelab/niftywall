<p align="center">
  <a href="README_ENG.md">
    <img src="https://img.shields.io/badge/🇬🇧_English-00D4FF?style=for-the-badge&logo=readme&logoColor=white" alt="English README">
  </a>
  <a href="README.md">
    <img src="https://img.shields.io/badge/🇺🇦_Українська-FF4D00?style=for-the-badge&logo=readme&logoColor=white" alt="Ukrainian version">
  </a>
</p>

<br>

<p align="center">
  <img src="https://img.shields.io/github/v/release/weby-homelab/niftywall?style=for-the-badge&color=emerald" alt="Latest Release">
  <img src="https://img.shields.io/badge/Branch-main_(Docker)-00b894?style=for-the-badge&logo=docker&logoColor=white" alt="Branch Main">
  <img src="https://img.shields.io/badge/Security-Hardened-blueviolet?style=for-the-badge&logo=securityscorecard&logoColor=white" alt="Security">
  <img src="https://img.shields.io/docker/pulls/webyhomelab/niftywall?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Pulls">
</p>

# 🛡️ NiftyWall v3.0.0 "Hardened" - Docker Edition [![Latest Release](https://img.shields.io/github/v/release/weby-homelab/niftywall)](https://github.com/weby-homelab/niftywall/releases/latest)

*Making Linux Firewalls Transparent, Smart, and Beautiful.*

**NiftyWall** is a professional web dashboard for managing the nftables firewall. In the v3.0.0 update, the project underwent a full audit to achieve Enterprise-grade stability and security. This edition (`main`) is optimized for rapid deployment in an isolated Docker environment.

---

## 🧩 System Architecture

```mermaid
graph TD
    User((Administrator)) -->|HTTPS / PWA| UI[Web Dashboard]
    
    subgraph "NiftyWall Core"
        UI -->|REST API / JWT| API[FastAPI Backend]
        API -->|Subprocess / JSON| NFT[nftables Engine]
        API -->|Log Analysis| F2B[Fail2Ban Parser]
        API -->|Metrics| SYS[psutil System Monitor]
        API -->|Persistence| DB[(SQLite Database)]
    end

    subgraph "Linux Kernel"
        NFT -->|Netlink| Netfilter[Kernel Hooks]
        Netfilter -->|Packet Counters| NFT
    end

    F2B -.->|GeoIP| WHO[Whois API]
```

---

## 🚀 What's New in v3.0.0 "Hardened"

- **🔐 SQLite Backend:** All states migrated to a reliable SQLite database. Resolved Race Conditions.
- **🛡️ Strict Input Validation:** Rigorous input validation via Pydantic. Full protection against NFT injections.
- **🕰️ Isolated Time Machine:** Backup and Restore work exclusively with the `niftywall` table, without affecting Docker or VPN rules.
- **🔄 Smart DNAT + SNAT:** Automatic addition of Masquerade rules to eliminate asymmetric routing issues.
- **🕵️ Resilient Fail2Ban:** New parsing logic capable of querying status directly via `fail2ban-client`.

---

## 🛠️ Installation (Docker Edition)

This method ensures full code isolation from the host system while utilizing necessary Kernel Hooks.

### 1. Prerequisites
- **Docker Engine** 24.0+ and **Docker Compose** v2.
- `nftables` present on the host system (for kernel module loading).

### 2. Deployment via Docker Compose
Create `docker-compose.yml`:

```yaml
services:
  niftywall:
    image: webyhomelab/niftywall:latest
    container_name: niftywall
    privileged: true # Required for nftables management
    network_mode: host # Required for direct interface access
    restart: always
    environment:
      - SECRET_KEY=${SECRET_KEY} # openssl rand -hex 32
      - PANIC_ALLOWED_PORTS=22,80,443,54322
      - TZ=Europe/Kyiv
    volumes:
      - /var/log/fail2ban.log:/var/log/fail2ban.log:ro
      - /var/run/fail2ban:/var/run/fail2ban
      - /opt/niftywall/data:/app/data
      - /opt/niftywall/snapshots:/app/snapshots
```

### 3. Run
```bash
docker compose up -d
```

---

## 📋 Detailed System Requirements and Environments

NiftyWall is built on the principle of **absolute autonomy**. By utilizing an isolated `inet niftywall` table with high-priority chains, the system ensures stability in complex network environments.

### 🟢 1. Ideal Environment (Native Bare Metal / Cloud VPS)
*Servers without additional third-party firewall layers.*
- **How it works:** NiftyWall acts as the sole master of network traffic. It initializes `input` and `forward` chains with type `filter` and **priority -100**, allowing packet processing at the very beginning of the kernel network stack.
- **Features:** Highest rule processing speed, 100% predictability, and zero overhead.

### 🟡 2. Mixed Environment (Servers with Docker / LXC / KVM)
*Servers actively utilizing containerization.*
- **Compatibility:** **Full (v2.0+).** NiftyWall no longer conflicts with Docker.
- **"Shield-First" Concept:** Thanks to **priority -100**, NiftyWall rules trigger **BEFORE** Docker's rules (which typically have priority 0). This allows you to block threats at the kernel level before they ever reach the virtual container bridges.
- **Isolation:** Operating in its own namespace (`table inet niftywall`) prevents accidental deletion of Docker rules during configuration resets.

### 🔴 3. Hostile Environment (UFW or Firewalld active)
*Servers where another high-level manager is already active.*
- **Compatibility:** **Not Recommended.**
- **The "Shadowing" Problem:** `nftables` allows multiple tables to work in parallel. A packet must be allowed in **both** systems simultaneously. If NiftyWall allows traffic but a forgotten UFW blocks it, you will face hard-to-diagnose issues.
- **Solution:** It is recommended to execute `systemctl disable --now ufw` or `firewalld` before using NiftyWall. If you specifically need a GUI for them, use: [UFW-GUI](https://github.com/weby-homelab/ufw-gui) or [Firewalld-GUI](https://github.com/weby-homelab/firewalld-gui).

---
<p align="center">
  Made with ❤️ in Kyiv under air raid sirens and blackouts<br>
  <strong>✦ 2026 Weby Homelab ✦</strong>
</p>
