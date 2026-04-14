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
        """Unbans an IP using fail2ban-client."""
        if not re.match(r"^[\d\.:a-fA-F]+$", ip):
            print(f"Invalid IP format: {ip}")
            return False
            
        try:
            # Most modern versions support global unban
            cmd = ["fail2ban-client", "unban", ip]
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            # Fallback to jail-specific unban if provided
            if jail:
                if not re.match(r"^[\w\-]+$", jail):
                    print(f"Invalid jail format: {jail}")
                    return False
                try:
                    cmd = ["fail2ban-client", "set", jail, "unbanip", ip]
                    subprocess.run(cmd, capture_output=True, check=True)
                    return True
                except: pass
            print(f"Error unbanning IP {ip}: {e}")
            return False

    def get_ban_info_for_ips(self, ips: list) -> Dict[str, dict]:
        """
        Scans the log file backwards (efficiently) if exists.
        Otherwise, probes fail2ban-client for status.
        """
        results = {}
        target_ips = set(ips)
        
        if not target_ips:
            return results

        # 1. Try Log File (Detailed info)
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'rb') as f:
                    f.seek(0, 2)
                    file_size = f.tell()
                    buffer_size = 8192
                    position = file_size
                    remainder = b''
                    
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

        # 2. Probe fail2ban-client for remaining IPs (Real-time check)
        if target_ips:
            try:
                j_out = subprocess.run(["fail2ban-client", "status"], capture_output=True, text=True)
                if j_out.returncode == 0:
                    j_match = re.search(r"Jail list:\s+(.*)", j_out.stdout)
                    if j_match:
                        jails = [j.strip() for j in j_match.group(1).split(",")]
                        for jail in jails:
                            s_out = subprocess.run(["fail2ban-client", "status", jail], capture_output=True, text=True)
                            if s_out.returncode == 0:
                                for tip in list(target_ips):
                                    if tip in s_out.stdout:
                                        results[tip] = {"jail": jail, "time": "active"}
                                        target_ips.remove(tip)
                                        if not target_ips: break
            except: pass
            
        return results
