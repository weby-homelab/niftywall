import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add app directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.fail2ban_parser import Fail2BanParser

class TestFail2BanParser(unittest.TestCase):
    def setUp(self):
        self.parser = Fail2BanParser(log_path="/tmp/f2b_test.log")

    @patch('app.fail2ban_parser.subprocess.run')
    @patch('app.fail2ban_parser.os.path.exists')
    def test_unban_ip_valid(self, mock_exists, mock_run):
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test valid IP
        result = self.parser.unban_ip("192.168.1.100")
        self.assertTrue(result)
        mock_run.assert_called_with(["/usr/bin/fail2ban-client", "unban", "192.168.1.100"], capture_output=True, check=True)

    @patch('app.fail2ban_parser.subprocess.run')
    def test_unban_ip_invalid(self, mock_run):
        # Test invalid IP (injection attempt)
        result = self.parser.unban_ip("192.168.1.100; rm -rf /")
        self.assertFalse(result)
        mock_run.assert_not_called()

    @patch('app.fail2ban_parser.subprocess.run')
    @patch('app.fail2ban_parser.os.path.exists')
    def test_unban_ip_with_jail(self, mock_exists, mock_run):
        mock_exists.return_value = True
        # First call (global unban) fails, triggering fallback
        mock_run.side_effect = [Exception("Global unban failed"), MagicMock(returncode=0)]
        
        result = self.parser.unban_ip("192.168.1.100", jail="sshd")
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_called_with(["/usr/bin/fail2ban-client", "set", "sshd", "unbanip", "192.168.1.100"], capture_output=True, check=True)

    @patch('app.fail2ban_parser.subprocess.run')
    @patch('app.fail2ban_parser.os.path.exists')
    def test_unban_ip_invalid_jail(self, mock_exists, mock_run):
        mock_exists.return_value = True
        mock_run.side_effect = Exception("Global unban failed")
        
        result = self.parser.unban_ip("192.168.1.100", jail="sshd; rm -rf /")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
