import subprocess
import re
import os
from typing import Dict, Optional

class Fail2BanParser:
    def __init__(self, log_path: str = "/var/log/fail2ban.log"):
        self.log_path = log_path
        # Example log line:
        # 2026-03-12 14:30:15,123 fail2ban.actions [1234]: NOTICE  [sshd] Ban 192.168.1.100
        self.ban_pattern = re.compile(r"^([\d\-]+ [\d:]+),\d+.*?\[([^\]]+)\] (Ban|Restore Ban) ([\d\.:a-fA-F]+)")

    def unban_ip(self, ip: str, jail: str = None) -> bool:
        """Unbans an IP using fail2ban-client. If jail is not provided, tries to find it."""
        try:
            if not jail:
                # Try to get jail info from log
                info = self.get_ban_info_for_ips([ip])
                if ip in info:
                    jail = info[ip]['jail']
                else:
                    return False
            
            cmd = ["fail2ban-client", "unban", ip]
            # Some versions might require jail name
            # cmd = ["fail2ban-client", "set", jail, "unbanip", ip]
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"Error unbanning IP {ip}: {e}")
            return False

    def get_ban_info_for_ips(self, ips: list) -> Dict[str, dict]:
        """
        Scans the log file backwards (efficiently) and returns the latest ban reason and time for the given IPs.
        """
        results = {}
        target_ips = set(ips)
        
        if not target_ips or not os.path.exists(self.log_path):
            return results

        try:
            # We read the file from the end to find the most recent bans quickly
            with open(self.log_path, 'rb') as f:
                # Seek to end
                f.seek(0, 2)
                file_size = f.tell()
                buffer_size = 8192
                position = file_size
                remainder = b''
                
                # Stop when we found info for all requested IPs or reached start of file
                while position > 0 and target_ips:
                    read_size = min(buffer_size, position)
                    position -= read_size
                    f.seek(position)
                    chunk = f.read(read_size) + remainder
                    
                    lines = chunk.split(b'\n')
                    remainder = lines[0]
                    lines = lines[1:]
                    
                    for line in reversed(lines):
                        if b'Ban ' not in line:
                            continue
                            
                        try:
                            decoded_line = line.decode('utf-8', errors='ignore')
                            match = self.ban_pattern.search(decoded_line)
                            if match:
                                timestamp = match.group(1)
                                jail = match.group(2)
                                ip = match.group(4)
                                
                                if ip in target_ips:
                                    results[ip] = {
                                        "jail": jail,
                                        "time": timestamp
                                    }
                                    target_ips.remove(ip)
                                    if not target_ips:
                                        break
                        except Exception:
                            continue
        except Exception as e:
            print(f"Error parsing fail2ban log: {e}")
            
        return results
