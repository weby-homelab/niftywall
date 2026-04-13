import json
import subprocess
import os
import glob
from datetime import datetime
from typing import Dict, Any

SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "snapshots")

class NftablesHandler:
    def __init__(self):
        self.nft_cmd = "/usr/sbin/nft"
        if not os.path.exists(SNAPSHOT_DIR):
            os.makedirs(SNAPSHOT_DIR)
        self.initialize_niftywall_table()

    def initialize_niftywall_table(self):
        """Creates an isolated NiftyWall table with high priority chains."""
        rules = """
        add table inet niftywall
        add chain inet niftywall nw-input { type filter hook input priority -100; policy accept; }
        add chain inet niftywall nw-forward { type filter hook forward priority -100; policy accept; }
        add chain inet niftywall nw-prerouting { type nat hook prerouting priority -150; policy accept; }
        add chain inet niftywall nw-postrouting { type nat hook postrouting priority 150; policy accept; }
        """
        try:
            subprocess.run([self.nft_cmd, "-f", "-"], input=rules, text=True, check=True)
        except Exception as e:
            print(f"Failed to initialize NiftyWall table: {e}")

    def _create_snapshot(self, action_name: str):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_action = "".join([c if c.isalnum() else "_" for c in action_name])
            filename = f"{timestamp}_{safe_action}.nft"
            filepath = os.path.join(SNAPSHOT_DIR, filename)
            
            result = subprocess.run([self.nft_cmd, "list", "ruleset"], capture_output=True, text=True, check=True)
            with open(filepath, 'w') as f:
                f.write(result.stdout)
                
            snapshots = sorted(glob.glob(os.path.join(SNAPSHOT_DIR, "*.nft")))
            if len(snapshots) > 20:
                for old_snap in snapshots[:-20]:
                    os.remove(old_snap)
            return filename
        except Exception as e:
            print(f"Snapshot creation failed: {e}")
            return None

    def list_snapshots(self) -> list:
        snapshots = []
        try:
            files = sorted(glob.glob(os.path.join(SNAPSHOT_DIR, "*.nft")), reverse=True)
            for file in files:
                basename = os.path.basename(file)
                parts = basename.replace(".nft", "").split("_", 2)
                if len(parts) >= 3:
                    date_str, time_str, action = parts[0], parts[1], parts[2]
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    snapshots.append({
                        "filename": basename,
                        "timestamp": dt.isoformat(),
                        "action": action.replace("_", " ")
                    })
        except Exception as e:
            pass
        return snapshots

    def restore_snapshot(self, filename: str) -> bool:
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        if not os.path.exists(filepath): return False
        try:
            subprocess.run([self.nft_cmd, "flush", "ruleset"], check=True)
            subprocess.run([self.nft_cmd, "-f", filepath], check=True)
            return True
        except: return False

    def get_ruleset(self) -> Dict[str, Any]:
        try:
            result = subprocess.run([self.nft_cmd, "-j", "list", "ruleset"], capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to execute nft: {e.stderr or e.stdout}"}
        except json.JSONDecodeError: return {"error": "JSON parse error"}
        except FileNotFoundError: return {"error": "nft missing"}

    def backup_ruleset(self, backup_path: str = "/etc/nftables.conf.backup") -> bool:
        try:
            result = subprocess.run([self.nft_cmd, "list", "ruleset"], capture_output=True, text=True, check=True)
            with open(backup_path, 'w') as f: f.write(result.stdout)
            return True
        except: return False

    def delete_rule(self, family: str, table: str, chain: str, handle: int) -> bool:
        self._create_snapshot(f"delete_rule_{handle}")
        try:
            subprocess.run([self.nft_cmd, "delete", "rule", family, table, chain, "handle", str(handle)], check=True)
            return True
        except: return False

    def add_advanced_rule(self, family: str, table: str, chain: str, protocol: str, ports: str, source: str, action: str, rate_enabled: bool, rate: int, unit: str, burst: int) -> dict:
        self._create_snapshot(f"add_advanced_rule_{protocol}_{ports}")
        commands = []
        port_str = f"{{ {ports} }}" if "," in ports else ports
        match_expr = f"{protocol} dport {port_str}"
        
        if source and source.lower() not in ["any", "0.0.0.0/0", "::/0"]:
            ip_ver = "ip6" if ":" in source else "ip"
            match_expr = f"{ip_ver} saddr {source} {match_expr}"
        
        if rate_enabled:
            set_name = f"limit_{protocol}_{ports.replace(',', '_')}"
            commands.append(f"add set inet niftywall {set_name} {{ type ipv4_addr; size 65536; flags dynamic, timeout; timeout 1h; }}")
            commands.append(f"add rule inet niftywall {chain} {match_expr} update @{set_name} {{ ip saddr limit rate {rate}/{unit} burst {burst} packets }} counter {action}")
            commands.append(f"add rule inet niftywall {chain} {match_expr} counter drop")
        else:
            commands.append(f"add rule inet niftywall {chain} {match_expr} counter {action}")

        try:
            process = subprocess.run([self.nft_cmd, "-f", "-"], input="\n".join(commands), text=True, capture_output=True)
            if process.returncode != 0: return {"success": False, "message": process.stderr}
            return {"success": True, "message": "Rule applied successfully"}
        except Exception as e: return {"success": False, "message": str(e)}

    def get_sets(self) -> Dict[str, Any]:
        try:
            result = subprocess.run([self.nft_cmd, "-j", "list", "sets"], capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except: return {"error": "Fetch sets failed"}

    def add_set_element(self, family: str, table: str, set_name: str, element: str) -> bool:
        self._create_snapshot(f"add_to_set_{set_name}")
        try:
            subprocess.run([self.nft_cmd, "add", "element", family, table, set_name, "{", element, "}"], check=True)
            return True
        except: return False

    def delete_set_element(self, family: str, table: str, set_name: str, element: str) -> bool:
        self._create_snapshot(f"remove_from_set_{set_name}")
        try:
            subprocess.run([self.nft_cmd, "delete", "element", family, table, set_name, "{", element, "}"], check=True)
            return True
        except: return False

    def add_dnat_rule(self, family: str, table: str, chain: str, protocol: str, external_port: int, internal_ip: str, internal_port: int) -> dict:
        self._create_snapshot("add_nat_rule")
        match_expr = f"{protocol} dport {external_port}"
        target = f"[{internal_ip}]:{internal_port}" if ":" in internal_ip and internal_port else f"{internal_ip}:{internal_port}" if internal_port else internal_ip
        
        ip_ver = "ip6" if ":" in internal_ip else "ip"
        dnat_cmd = f"add rule inet niftywall nw-prerouting {match_expr} counter dnat {ip_ver} to {target}"
        fwd_port = internal_port if internal_port else external_port
        
        fwd_cmd = f"add rule inet niftywall nw-forward {ip_ver} daddr {internal_ip} {protocol} dport {fwd_port} counter accept"

        try:
            process = subprocess.run([self.nft_cmd, "-f", "-"], input=f"{dnat_cmd}\n{fwd_cmd}", text=True, capture_output=True)
            if process.returncode != 0: return {"success": False, "message": process.stderr}
            return {"success": True, "message": "NAT Rule applied successfully"}
        except Exception as e: return {"success": False, "message": str(e)}

    def apply_panic_mode(self) -> bool:
        self._create_snapshot("panic_mode")
        rules = """
        flush chain inet niftywall nw-input
        add rule inet niftywall nw-input iif "lo" accept
        add rule inet niftywall nw-input ct state established,related accept
        add rule inet niftywall nw-input icmp type echo-request accept
        add rule inet niftywall nw-input icmpv6 type echo-request accept
        add rule inet niftywall nw-input tcp dport { 22, 8080, 54322 } accept
        add rule inet niftywall nw-input iifname "tailscale0" accept
        add rule inet niftywall nw-input counter drop
        """
        try:
            subprocess.run([self.nft_cmd, "-f", "-"], input=rules, text=True, check=True)
            return True
        except: return False
