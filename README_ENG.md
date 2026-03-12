# 🛡️ NiftyWall v1.3.0
*Making Linux Firewalls Transparent, Smart, and Beautiful.*

**NiftyWall** (formerly NFTables Dashboard) is a lightweight, secure, and modern web dashboard for viewing and managing `nftables` firewall configurations on Linux servers (specifically optimized for Ubuntu 24.04).

It interacts directly with the Linux kernel (bypassing wrappers like `firewalld` or `ufw`) and translates complex terminal output into a user-friendly tool with real-time analytics. Perfect for Docker-heavy environments.

## ✨ What's New in v1.3.0 (Anti-DDoS & NAT Edition)

- **🔀 Smart NAT Management (Port Forwarding):** A dedicated tab for setting up DNAT rules to forward external traffic to internal services (e.g., Docker containers). NiftyWall automatically adds the required `accept` rules in the `FORWARD` chain to ensure traffic flows seamlessly.
- **🛡️ Rule Builder with Anti-DDoS:** A new modal for building complex rules. You can now enforce strict **Rate Limits** (e.g., 30 requests/sec) to protect your services from floods and DDoS attacks.
- **🕵️‍♂️ Fail2Ban Integration:** NiftyWall parses your `/var/log/fail2ban.log` and displays the exact ban reason (e.g., `Jail: sshd`) and timestamp next to every blocked IP address in the Dynamic Sets tab.
- **🌍 Intelligent Geo-Location:** Automatically detect country and city for IP addresses in your Sets.
- **📈 Live Activity Charts (Sparklines):** Real-time traffic visualization for every rule. See activity spikes instantly without refreshing the page (powered by Chart.js).
- **📜 Audit Log:** Full history of all user actions in the system. Track who changed what rule and when.

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
