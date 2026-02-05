"""Tests for loading service configuration."""

import sys
import unittest
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import load_services, find_service

SERVICES_TOML = Path(__file__).parent.parent / "skills" / "status-page" / "services.toml"


class TestLoadServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.services = load_services(SERVICES_TOML)

    def test_loads_services(self):
        self.assertGreater(len(self.services), 0)

    def test_loads_claude_service(self):
        self.assertIn("claude", self.services)

    def test_claude_has_feed_url(self):
        self.assertEqual(self.services["claude"]["feed"], "https://status.claude.com/history.atom")


class TestFindService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.services = load_services(SERVICES_TOML)

    def test_finds_by_key(self):
        key, service = find_service(self.services, "claude")
        self.assertEqual(key, "claude")
        self.assertEqual(service["name"], "Claude")

    def test_finds_by_alias(self):
        key, service = find_service(self.services, "anthropic")
        self.assertEqual(key, "claude")  # Returns canonical key, not alias
        self.assertEqual(service["name"], "Claude")

    def test_finds_github_by_alias(self):
        key, service = find_service(self.services, "gh")
        self.assertEqual(key, "github")
        self.assertEqual(service["name"], "GitHub")

    def test_returns_none_for_unknown(self):
        result = find_service(self.services, "unknown-service")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
