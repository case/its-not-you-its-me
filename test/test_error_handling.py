"""Tests for error handling with malformed input."""

import sys
import unittest
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import (
    FeedParseError,
    parse_atom_feed,
    parse_rss_feed,
    extract_status_from_html,
)


class TestMalformedXml(unittest.TestCase):
    def test_atom_feed_raises_on_invalid_xml(self):
        with self.assertRaises(FeedParseError) as ctx:
            parse_atom_feed("not valid xml <<<<")
        self.assertIn("Invalid XML", str(ctx.exception))

    def test_rss_feed_raises_on_invalid_xml(self):
        with self.assertRaises(FeedParseError) as ctx:
            parse_rss_feed("not valid xml <<<<")
        self.assertIn("Invalid XML", str(ctx.exception))

    def test_atom_feed_raises_on_empty_string(self):
        with self.assertRaises(FeedParseError):
            parse_atom_feed("")

    def test_rss_feed_raises_on_empty_string(self):
        with self.assertRaises(FeedParseError):
            parse_rss_feed("")


class TestEmptyFeed(unittest.TestCase):
    def test_atom_feed_returns_empty_list_for_no_entries(self):
        xml = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        incidents = parse_atom_feed(xml)
        self.assertEqual(incidents, [])

    def test_rss_feed_returns_empty_list_for_no_items(self):
        xml = '<?xml version="1.0"?><rss><channel></channel></rss>'
        incidents = parse_rss_feed(xml)
        self.assertEqual(incidents, [])


class TestMissingFields(unittest.TestCase):
    def test_atom_feed_handles_missing_fields(self):
        xml = '''<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry></entry>
        </feed>'''
        incidents = parse_atom_feed(xml)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].title, "")
        self.assertEqual(incidents[0].link, "")
        self.assertEqual(incidents[0].status, "Unknown")

    def test_rss_feed_handles_missing_fields(self):
        xml = '''<?xml version="1.0"?>
        <rss><channel><item></item></channel></rss>'''
        incidents = parse_rss_feed(xml)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].title, "")
        self.assertEqual(incidents[0].link, "")
        self.assertEqual(incidents[0].status, "Unknown")


class TestExtractStatus(unittest.TestCase):
    def test_returns_unknown_for_empty_content(self):
        self.assertEqual(extract_status_from_html(""), "Unknown")

    def test_returns_unknown_for_no_status_markers(self):
        self.assertEqual(extract_status_from_html("<p>No status here</p>"), "Unknown")

    def test_extracts_first_status(self):
        html = "<strong>Investigating</strong> then <strong>Resolved</strong>"
        self.assertEqual(extract_status_from_html(html), "Investigating")


if __name__ == "__main__":
    unittest.main()
