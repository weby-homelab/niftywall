import json
import subprocess
from typing import Dict, Any

class NftablesHandler:
    def __init__(self):
        # Use full path for the nft binary
        self.nft_cmd = "/usr/sbin/nft"

    def get_ruleset(self) -> Dict[str, Any]:
        """
        Executes 'nft -j list ruleset' and returns the parsed JSON.
        """
        try:
            result = subprocess.run(
                [self.nft_cmd, "-j", "list", "ruleset"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to execute nft: {e.stderr or e.stdout or str(e)}"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse nftables JSON output"}
        except FileNotFoundError:
            return {"error": "nft command not found. Is nftables installed?"}

    def backup_ruleset(self, backup_path: str = "/etc/nftables.conf.backup") -> bool:
        """
        Backs up the current ruleset to a file using 'nft list ruleset'.
        """
        try:
            result = subprocess.run(
                [self.nft_cmd, "list", "ruleset"],
                capture_output=True,
                text=True,
                check=True
            )
            with open(backup_path, 'w') as f:
                f.write(result.stdout)
            return True
        except Exception as e:
            print(f"Backup error: {e}")
            return False

    def delete_rule(self, family: str, table: str, chain: str, handle: int) -> bool:
        """
        Deletes a specific rule by its handle.
        Command: nft delete rule <family> <table> <chain> handle <handle>
        """
        try:
            subprocess.run(
                [self.nft_cmd, "delete", "rule", family, table, chain, "handle", str(handle)],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to delete rule: {e}")
            return False

    def add_port_rule(self, family: str, table: str, chain: str, port: int, protocol: str) -> bool:
        """
        Adds a rule to accept traffic on a specific port. (Legacy simple method)
        """
        try:
            subprocess.run(
                [self.nft_cmd, "add", "rule", family, table, chain, protocol, "dport", str(port), "counter", "accept"],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to add port: {e}")
            return False

    def add_advanced_rule(self, family: str, table: str, chain: str, protocol: str, ports: str, source: str, action: str, rate_enabled: bool, rate: int, unit: str, burst: int) -> dict:
        """
        Builds and applies a complex nftables rule including optional rate limiting via dynamic sets.
        Returns a dict with {"success": bool, "message": str}
        """
        commands = []
        
        # Format ports. If comma-separated, wrap in {}
        port_str = f"{{ {ports} }}" if "," in ports else ports
        
        # Base match expression
        match_expr = f"{protocol} dport {port_str}"
        
        # Add source IP if it's not 'any'
        if source and source.lower() not in ["any", "0.0.0.0/0", "::/0"]:
            ip_ver = "ip6" if ":" in source else "ip"
            match_expr = f"{ip_ver} saddr {source} {match_expr}"
        
        if rate_enabled:
            # For rate limiting, we need a dynamic set to track IPs
            set_name = f"limit_{protocol}_{ports.replace(',', '_')}"
            ip_type = "ipv6_addr" if family == "ip6" else "ipv4_addr"
            
            # Command 1: Create the set if it doesn't exist (we ignore errors if it exists)
            set_cmd = f"add set {family} {table} {set_name} {{ type {ip_type}; size 65536; flags dynamic, timeout; timeout 1h; }}"
            commands.append(set_cmd)
            
            # Command 2: The actual rate limit rule
            saddr_var = "ip6 saddr" if family == "ip6" else "ip saddr"
            limit_cmd = f"add rule {family} {table} {chain} {match_expr} update @{set_name} {{ {saddr_var} limit rate {rate}/{unit} burst {burst} packets }} counter {action}"
            commands.append(limit_cmd)
            
            # Command 3: Drop everything else that exceeds the limit for these ports
            drop_cmd = f"add rule {family} {table} {chain} {match_expr} counter drop"
            commands.append(drop_cmd)
        else:
            # Simple rule without limits
            cmd = f"add rule {family} {table} {chain} {match_expr} counter {action}"
            commands.append(cmd)

        # Execute commands using nft -f -
        full_command_str = "\n".join(commands)
        try:
            process = subprocess.run(
                [self.nft_cmd, "-f", "-"], 
                input=full_command_str, 
                text=True, 
                capture_output=True
            )
            if process.returncode != 0:
                return {"success": False, "message": f"NFTables error: {process.stderr}"}
            return {"success": True, "message": "Rule applied successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_sets(self) -> Dict[str, Any]:
        """
        Executes 'nft -j list sets' and returns the parsed JSON.
        """
        try:
            result = subprocess.run(
                [self.nft_cmd, "-j", "list", "sets"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": f"Failed to fetch sets: {str(e)}"}

    def add_set_element(self, family: str, table: str, set_name: str, element: str) -> bool:
        """
        Adds an element to a set.
        Command: nft add element <family> <table> <set_name> { <element> }
        """
        try:
            subprocess.run(
                [self.nft_cmd, "add", "element", family, table, set_name, "{", element, "}"],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to add set element: {e}")
            return False

    def delete_set_element(self, family: str, table: str, set_name: str, element: str) -> bool:
        """
        Deletes an element from a set.
        Command: nft delete element <family> <table> <set_name> { <element> }
        """
        try:
            # Note: for prefixes or specific types, formatting might need care
            subprocess.run(
                [self.nft_cmd, "delete", "element", family, table, set_name, "{", element, "}"],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to delete set element: {e}")
            return False

    def add_dnat_rule(self, family: str, table: str, chain: str, protocol: str, external_port: int, internal_ip: str, internal_port: int) -> dict:
        """
        Adds a DNAT (Port Forwarding) rule.
        Also adds a corresponding accept rule in the forward chain so traffic isn't dropped.
        """
        match_expr = f"{protocol} dport {external_port}"
        
        # For IPv6, the internal IP must be wrapped in brackets [ ] for dnat if it includes a port
        if ":" in internal_ip and internal_port:
            target = f"[{internal_ip}]:{internal_port}"
        else:
            target = f"{internal_ip}:{internal_port}" if internal_port else internal_ip

        # Command 1: The actual NAT rule
        dnat_cmd = f"add rule {family} {table} {chain} {match_expr} counter dnat to {target}"
        
        # Command 2: Allow the forwarded traffic through the firewall
        # Assuming the standard filter table and forward chain
        fwd_port = internal_port if internal_port else external_port
        ip_ver = "ip6" if ":" in internal_ip else "ip"
        fwd_cmd = f"add rule inet filter forward {ip_ver} daddr {internal_ip} {protocol} dport {fwd_port} counter accept"

        full_command_str = f"{dnat_cmd}\n{fwd_cmd}"

        try:
            process = subprocess.run(
                [self.nft_cmd, "-f", "-"], 
                input=full_command_str, 
                text=True, 
                capture_output=True
            )
            if process.returncode != 0:
                return {"success": False, "message": f"NFTables error: {process.stderr}"}
            return {"success": True, "message": "NAT and Forwarding rules applied successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def apply_panic_mode(self) -> bool:
        """
        Panic mode: flushes the input chain and only allows established connections,
        lo interface, SSH (22, 54322) and Tailscale traffic (tailscale0).
        """
        rules = """
        flush chain inet filter input
        add rule inet filter input iif "lo" accept
        add rule inet filter input ct state established,related accept
        add rule inet filter input icmp type echo-request accept
        add rule inet filter input icmpv6 type echo-request accept
        add rule inet filter input tcp dport { 22, 54322 } accept
        add rule inet filter input iifname "tailscale0" accept
        """
        try:
            subprocess.run([self.nft_cmd, "-f", "-"], input=rules, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Panic mode failed: {e}")
            return False
