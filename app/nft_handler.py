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
        Adds a rule to accept traffic on a specific port.
        Command: nft add rule <family> <table> <chain> <protocol> dport <port> counter accept
        We default to 'inet filter input' if not specified, but we take params to be safe.
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
