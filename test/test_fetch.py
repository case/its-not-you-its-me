"""Tests for feed fetching with mocked network."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import FeedCache, fetch_feed


class MockResponse:
    """Mock HTTP response."""
    def __init__(self, content: bytes, headers: dict = None):
        self.content = content
        self.headers = headers or {}

    def read(self):
        return self.content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestFetchFeed(unittest.TestCase):
    @patch("check_status.urllib.request.urlopen")
    def test_fetches_content_from_url(self, mock_urlopen):
        mock_urlopen.return_value = MockResponse(b"<feed>test</feed>")

        content = fetch_feed("https://example.com/feed.atom")

        self.assertEqual(content, "<feed>test</feed>")
        mock_urlopen.assert_called_once()

    @patch("check_status.urllib.request.urlopen")
    def test_uses_cache_when_fresh(self, mock_urlopen):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FeedCache(Path(tmpdir))
            cache.store("test", "<feed>cached</feed>")

            # Should not call urlopen because cache is fresh
            content = fetch_feed(
                "https://example.com/feed.atom",
                cache=cache,
                cache_key="test",
                max_age_seconds=60
            )

            self.assertEqual(content, "<feed>cached</feed>")
            mock_urlopen.assert_not_called()

    @patch("check_status.urllib.request.urlopen")
    def test_fetches_when_cache_stale(self, mock_urlopen):
        mock_urlopen.return_value = MockResponse(b"<feed>fresh</feed>")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FeedCache(Path(tmpdir))
            cache.store("test", "<feed>stale</feed>")

            # max_age_seconds=0 means cache is always stale
            content = fetch_feed(
                "https://example.com/feed.atom",
                cache=cache,
                cache_key="test",
                max_age_seconds=0
            )

            self.assertEqual(content, "<feed>fresh</feed>")
            mock_urlopen.assert_called_once()

    @patch("check_status.urllib.request.urlopen")
    def test_stores_etag_in_cache(self, mock_urlopen):
        response = MockResponse(b"<feed>test</feed>", headers={"ETag": '"abc123"'})
        mock_urlopen.return_value = response

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FeedCache(Path(tmpdir))

            fetch_feed(
                "https://example.com/feed.atom",
                cache=cache,
                cache_key="test",
                max_age_seconds=0
            )

            cached = cache.get("test")
            self.assertEqual(cached["etag"], '"abc123"')


if __name__ == "__main__":
    unittest.main()
