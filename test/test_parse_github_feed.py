"""Tests for parsing GitHub status feeds."""

import sys
import unittest
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import parse_atom_feed, parse_rss_feed

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "github"


class TestParseGitHubAtomFeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        content = (FIXTURES_DIR / "2026-02-04-history.atom").read_text()
        cls.incidents = parse_atom_feed(content)

    def test_parses_atom_feed(self):
        self.assertGreater(len(self.incidents), 0)

    def test_extracts_incident_title(self):
        titles = [i.title for i in self.incidents]
        self.assertIn("Delays in UI updates for Actions Runs", titles)

    def test_extracts_incident_link(self):
        incident = self.incidents[0]
        self.assertIn("githubstatus.com/incidents/", incident.link)

    def test_extracts_incident_status(self):
        # First incident should be resolved
        incident = self.incidents[0]
        self.assertEqual(incident.status, "Resolved")

    def test_extracts_published_date(self):
        incident = self.incidents[0]
        self.assertIn("2026-02", incident.published)


class TestParseGitHubRssFeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        content = (FIXTURES_DIR / "2026-02-04-history.rss").read_text()
        cls.incidents = parse_rss_feed(content)

    def test_parses_rss_feed(self):
        self.assertGreater(len(self.incidents), 0)

    def test_extracts_incident_title(self):
        titles = [i.title for i in self.incidents]
        self.assertIn("Delays in UI updates for Actions Runs", titles)

    def test_extracts_incident_link(self):
        incident = self.incidents[0]
        self.assertIn("githubstatus.com/incidents/", incident.link)

    def test_extracts_incident_status(self):
        incident = self.incidents[0]
        self.assertEqual(incident.status, "Resolved")


if __name__ == "__main__":
    unittest.main()
