# 🛡️ NFTables Dashboard v1.1.0

A lightweight, secure, and modern web dashboard for viewing and managing `nftables` firewall configurations on Linux servers.

Version **v1.1.0** transforms the basic interface into a powerful security analytics and dynamic management tool.

## ✨ What's New in v1.1.0

- **🌍 Intelligent Geo-Location:** Automatically detect country and city for IP addresses in your Sets. Know exactly where attacks or connections are coming from.
- **📈 Live Activity Charts (Sparklines):** Real-time traffic visualization for every rule. See activity spikes instantly without refreshing the page.
- **⚙️ Dynamic Sets Management:** A full interface to manage IP lists (e.g., `banned4` or `allow_list`). Add and remove addresses with a single click.
- **📜 Audit Log:** Full history of all user actions in the system. Track who changed what rule and when.
- **⚡ Performance Optimization:** Switched to asynchronous background data updates (polling) every 5 seconds.

## 🚀 Key Features

- **Visual Audit:** Complete overview of tables, chains, and rules in a clean, human-readable format.
- **Instant Port Opening:** Quick form to add allow rules for TCP/UDP traffic.
- **Panic Mode:** Emergency button to block all incoming traffic except essential services (SSH, Tailscale).
- **One-Click Backup:** Create an instant backup of the current firewall state to `/etc/nftables.conf.backup`.
- **Security First:** JWT-based authentication, Brute Force protection, and localhost-only binding (recommended access via SSH or Cloudflare Tunnel).

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/weby-homelab/nftables-dashboard.git
cd nftables-dashboard

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env, set your admin password and generate a secure SECRET_KEY
```

## 📋 System Requirements

- Python 3.10+
- `nftables` (with root privileges to execute commands)
- `uvicorn`, `FastAPI`, `PyJWT`, `bcrypt`

## 🛡️ Security

The dashboard binds to `127.0.0.1:8080` by default. This is intentional to ensure your firewall management isn't exposed to the public internet. To access it:
- **SSH Tunnel:** `ssh -L 8080:127.0.0.1:8080 user@your-server`
- **Cloudflare Tunnel:** configure `cloudflared` to proxy your internal port to a secured subdomain.

---
© 2026 Weby Homelab. Built for those who value control and aesthetics in system administration.
