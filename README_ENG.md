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
  <img src="https://img.shields.io/badge/Branch-classic_(Bare_Metal)-orange?style=for-the-badge&logo=linux&logoColor=white" alt="Branch Classic">
  <img src="https://img.shields.io/badge/Engine-nftables-blue?style=for-the-badge&logo=linux&logoColor=white" alt="Engine">
  <img src="https://img.shields.io/badge/Security-Hardened-blueviolet?style=for-the-badge&logo=securityscorecard&logoColor=white" alt="Security">
</p>

# 🛡️ NiftyWall v3.0.1 "Hardened" - Bare Metal Edition [![Latest Release](https://img.shields.io/github/v/release/weby-homelab/niftywall)](https://github.com/weby-homelab/niftywall/releases/latest)

*Making Linux Firewalls Transparent, Smart, and Beautiful.*

**NiftyWall** is a professional web dashboard for managing the nftables firewall. In the v3.0.1 update, the project underwent a full audit to achieve Enterprise-grade stability. This edition (`classic`) is optimized to run directly on the host system, providing maximum performance and direct access to the kernel's Netlink API.

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

## 🚀 What's New in v3.0.1 "Hardened"

- **🔐 SQLite Backend:** All states migrated to a reliable SQLite database. Resolved Race Conditions.
- **🛡️ Strict Input Validation:** Rigorous input validation via Pydantic. Full protection against NFT injections.
- **🕰️ Isolated Time Machine:** Backup and Restore work exclusively with the `niftywall` table, without affecting Docker or VPN rules.
- **🔄 Smart DNAT + SNAT:** Automatic addition of Masquerade rules to eliminate asymmetric routing issues.
- **🕵️ Resilient Fail2Ban:** New parsing logic capable of querying status directly via `fail2ban-client`.

---

## 🛠️ Installation (Bare Metal Edition)

Optimized for operation using Systemd and Uvicorn on pure Linux.

### 1. Prerequisites
- **Python** 3.10+
- **nftables** package (v1.0.9+)
- **fail2ban** package (for log analysis)
- **root** or **sudo** privileges

### 2. Step-by-Step Setup
```bash
# Clone the repository
git clone -b classic https://github.com/weby-homelab/niftywall.git /opt/niftywall
cd /opt/niftywall

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Generate SECRET_KEY: openssl rand -hex 32
```

### 3. Systemd Configuration
Create `/etc/systemd/system/niftywall.service`:
```ini
[Unit]
Description=NiftyWall Firewall Dashboard
After=network.target nftables.service

[Service]
User=root
WorkingDirectory=/opt/niftywall
ExecStart=/opt/niftywall/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
systemctl daemon-reload
systemctl enable --now niftywall
```

---

## 📋 Detailed System Requirements and Environments

### 🟢 1. Ideal Environment (Native Bare Metal / Cloud VPS)
*Transparent kernel management without intermediaries.*
- **How it works:** NiftyWall initializes the `inet niftywall` table in the `nftables` stack. It uses `filter` type for `input` and `forward` chains with **priority -100**, allowing packet processing at early stages of the network stack.
- **Features:** Highest rule processing speed and 100% predictability. No rule will be ignored by third-party services.

### 🟡 2. Mixed Environment (Servers with Docker / LXC / KVM)
*Harmonious coexistence with containerization.*
- **"Shield-First" Concept:** Thanks to **priority -100**, NiftyWall becomes the "first line of defense." Packets hit your rules **BEFORE** they are routed to the `DOCKER-USER` or `FORWARD` chains of the Docker package manager.
- **Table Isolation:** Operating in its own namespace (`table inet niftywall`) eliminates the risk of accidentally deleting Docker rules during configuration updates.

### 🔴 3. Hostile Environment (UFW or Firewalld active)
*Risk of conflicts and rule "shadowing".*
- **The Problem:** Since `nftables` allows multiple tables to work in parallel, a packet must be allowed in **both** systems simultaneously. This creates situations where NiftyWall allows traffic, but a legacy manager blocks it "in the shadow."
- **Solution:** It is recommended to execute `systemctl disable --now ufw` or `firewalld` before activating NiftyWall. If you specifically need a GUI for them, use: [UFW-GUI](https://github.com/weby-homelab/ufw-gui) or [Firewalld-GUI](https://github.com/weby-homelab/firewalld-gui).

---

## 📥 Other Options
For rapid deployment in an isolated environment, use the [main](https://github.com/weby-homelab/niftywall/tree/main) branch (Docker Edition).

---
<p align="center">
  Made with ❤️ in Kyiv under air raid sirens and blackouts<br>
  <strong>✦ 2026 Weby Homelab ✦</strong>
</p>
