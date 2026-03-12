import json
import subprocess
from typing import Dict, Any

class NftablesHandler:
    def __init__(self):
        # We assume the app is run as root or has sudo privileges for nft
        self.nft_cmd = "nft"

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
            return {"error": f"Failed to execute nft: {e.stderr}"}
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
