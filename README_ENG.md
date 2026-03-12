# 🛡️ NFTables Dashboard

[Українська версія](README.md)

A lightweight, secure, and modern web dashboard for viewing and managing `nftables` firewall configurations on Linux servers.

Built specifically for system administrators who manage `nftables` directly (without `firewalld` or other wrappers) and need a clean visual overview of their rules without parsing complex terminal output.

## ✨ Features
- **Native JSON API:** Interacts directly with the kernel via `nft -j list ruleset` (eliminating text parsing errors, ensuring 100% accuracy).
- **Rule Visualization:** Beautifully view Tables, Chains, Hooks, Policies, and individual rules with syntax highlighting (accept, drop, masquerade).
- **One-Click Backups:** Create an instant backup of the current firewall state to `/etc/nftables.conf.backup`.
- **High Security:** 
  - Robust authentication system (JWT tokens).
  - Password hashing using `bcrypt`.
  - Built-in Brute-force protection (Rate Limiting).
- **Modern Design (Glassmorphism):** The interface runs on a single HTML file using Tailwind CSS (via CDN) and Vanilla JS.
- **FastAPI Backend:** A fast and asynchronous Python-based backend.

## ⚠️ Security Notice
This application requires `root` privileges to execute `nft` commands. **IT IS STRICTLY PROHIBITED** to expose the port of this dashboard to the open internet.
It is designed to run locally (`127.0.0.1`) and must only be accessed via secure VPN tunnels (e.g., Tailscale, WireGuard), SSH port forwarding, or a securely configured Cloudflare Tunnel.

## 🚀 Installation & Running

1. **Clone the repository:**
   ```bash
   git clone https://github.com/weby-homelab/nftables-dashboard.git
   cd nftables-dashboard
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure credentials:**
   Copy the example or create a `.env` file in the project root:
   ```env
   ADMIN_USERNAME=your_username
   ADMIN_PASSWORD_HASH=your_bcrypt_hash
   SECRET_KEY=your_random_secret_key
   ```
   *To generate a bcrypt hash for your password, use:*
   `python -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"`

4. **Run the Dashboard (Must be run as root to access nft):**
   ```bash
   sudo venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
   ```

5. **Access the Dashboard:**
   Open `http://127.0.0.1:8080` in your browser (or set up a proxy/tunnel).

## 🛠 Deploying as a Systemd Service (Recommended)

To keep it running permanently in the background, create a systemd service:

Create `/etc/systemd/system/nftables-dashboard.service`:
```ini
[Unit]
Description=NFTables Web Dashboard
After=network.target

[Service]
User=root
WorkingDirectory=/root/geminicli/weby-homelab/nftables-dashboard
ExecStart=/root/geminicli/weby-homelab/nftables-dashboard/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
systemctl daemon-reload
systemctl enable nftables-dashboard.service
systemctl start nftables-dashboard.service
```

---
*© 2026 Weby Homelab*
