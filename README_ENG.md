<p align="center">
  <a href="README_ENG.md">
    <img src="https://img.shields.io/badge/🇬🇧_English-00D4FF?style=for-the-badge&logo=readme&logoColor=white" alt="English README">
  </a>
  <a href="README.md">
    <img src="https://img.shields.io/badge/🇺🇦_Українська-FF4D00?style=for-the-badge&logo=readme&logoColor=white" alt="Українська версія">
  </a>
</p>

# 🛡️ NiftyWall v1.4.1
*Making Linux Firewalls Transparent, Smart, and Beautiful.*

**NiftyWall** (formerly NFTables Dashboard) is a lightweight, secure, and modern web dashboard for viewing and managing `nftables` firewall configurations on Linux servers (specifically optimized for Ubuntu 24.04).

It interacts directly with the Linux kernel (bypassing wrappers like `firewalld` or `ufw`) and translates complex terminal output into a user-friendly tool with real-time analytics. Perfect for Docker-heavy environments.

## ✨ What's New in v1.4.1 (Smart Clone & Edit)

- **📝 Smart Clone (Rule Editing):** You can now edit any existing rule! The new "Clone" button next to a rule automatically pre-fills the Rule Builder modal with all the parameters of the old rule. Modify the port, IP, or limit and create an updated version in one click.
- **🕰️ Time Machine (Auto-Snapshots):** Feel safe making changes! Before any firewall mutation, NiftyWall automatically creates a snapshot of your current configuration.
- **🔀 Smart NAT Management (Port Forwarding):** A dedicated tab for setting up DNAT rules to forward external traffic to internal services (e.g., Docker containers). NiftyWall automatically adds the required `accept` rules in the `FORWARD` chain.
- **🛡️ Rule Builder with Anti-DDoS:** A new modal for building complex rules with strict rate limits.
- **🕵️‍♂️ Fail2Ban Integration:** Displays exact ban reasons (Jails) and timestamps next to blocked IP addresses.
- **🌍 Intelligent Geo-Location:** Automatically detect country and city for IP addresses.
- **📈 Live Activity Charts (Sparklines):** Real-time traffic visualization for every rule.
- **📜 Audit Log:** Full history of all user actions in the system.

## 🚀 Key Features

- **Human-Readable Formatting:** Forget raw JSON arrays. Rules are displayed as beautiful, color-coded badges (`TCP Port = 80, 443`, `DNAT ➔ 172.17.0.2`).
- **Dynamic Sets Management:** A full interface to manage IP lists (e.g., `banned4` or `allow_list`).
- **Panic Mode:** Emergency button to block all incoming traffic except essential services (SSH, Tailscale).
- **One-Click Backup:** Create an instant backup of the current firewall state to `/etc/nftables.conf.backup`.
- **Security First:** JWT-based authentication, Brute Force protection, and localhost-only binding.

## 🛠️ Installation (Ubuntu 24.04)

```bash
# 1. Clone the repository
git clone https://github.com/weby-homelab/niftywall.git
cd niftywall

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env, set your admin password and generate a secure SECRET_KEY
```

### Running as a Systemd Service (Recommended)
Create `/etc/systemd/system/niftywall.service`:

```ini
[Unit]
Description=NiftyWall Firewall Dashboard
After=network.target nftables.service

[Service]
User=root
Group=root
WorkingDirectory=/opt/niftywall
Environment="PATH=/opt/niftywall/venv/bin"
ExecStart=/opt/niftywall/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```
Then run: `systemctl daemon-reload && systemctl enable --now niftywall.service`

## 📋 System Requirements

- Ubuntu 24.04 (or any modern Linux with `nftables` 1.0.9+)
- Python 3.10+
- `root` privileges to execute `nft` commands.

---
© 2026 Weby Homelab. Built for those who value control and aesthetics in system administration.
