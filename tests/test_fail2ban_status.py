"""Fail2Ban status matches complete addresses, never substrings."""
from types import SimpleNamespace
from unittest.mock import patch

from app.fail2ban_parser import Fail2BanParser


def test_status_matches_exact_addresses(tmp_path):
    output = "Status for the jail: sshd\n|- Filter\n`- Actions\n   |- Currently banned: 2\n   `- Banned IP list: 11.2.3.40 2001:db8::2\n"
    def command(args, **kwargs):
        if len(args) == 2:
            return SimpleNamespace(returncode=0, stdout="Jail list: sshd\n")
        return SimpleNamespace(returncode=0, stdout=output)

    with patch("app.fail2ban_parser.subprocess.run", side_effect=command):
        result = Fail2BanParser(log_path=str(tmp_path / "absent")).get_ban_info_for_ips(
            ["1.2.3.4", "11.2.3.40", "2001:db8::2", "2001:db8::"]
        )

    assert set(result) == {"11.2.3.40", "2001:db8::2"}
    assert all(value["jail"] == "sshd" for value in result.values())
