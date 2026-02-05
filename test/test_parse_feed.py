"""Tests for parsing Atom and RSS status feeds."""

import sys
import unittest
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import parse_atom_feed, parse_rss_feed

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "claude"


class TestParseAtomFeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        content = (FIXTURES_DIR / "2026-02-04-history.atom").read_text()
        cls.incidents = parse_atom_feed(content)

    def test_parses_atom_feed(self):
        self.assertGreater(len(self.incidents), 0)

    def test_extracts_incident_title(self):
        self.assertEqual(self.incidents[0].title, "Elevated errors on Claude models")

    def test_extracts_incident_link(self):
        self.assertEqual(self.incidents[0].link, "https://status.claude.com/incidents/pvbysfjjrf8m")

    def test_extracts_incident_status(self):
        self.assertEqual(self.incidents[0].status, "Resolved")

    def test_extracts_published_date(self):
        self.assertEqual(self.incidents[0].published, "2026-02-04T17:06:50Z")


class TestParseRssFeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        content = (FIXTURES_DIR / "2026-02-04-history.rss").read_text()
        cls.incidents = parse_rss_feed(content)

    def test_parses_rss_feed(self):
        self.assertGreater(len(self.incidents), 0)

    def test_extracts_incident_title(self):
        self.assertEqual(self.incidents[0].title, "Elevated errors on Claude models")

    def test_extracts_incident_link(self):
        self.assertEqual(self.incidents[0].link, "https://status.claude.com/incidents/pvbysfjjrf8m")

    def test_extracts_incident_status(self):
        self.assertEqual(self.incidents[0].status, "Resolved")


if __name__ == "__main__":
    unittest.main()
