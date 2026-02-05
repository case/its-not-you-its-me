"""Tests for feed caching."""

import sys
import tempfile
import unittest
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import FeedCache


class TestFeedCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache = FeedCache(Path(self.temp_dir))

    def test_cache_miss_returns_none(self):
        result = self.cache.get("claude")
        self.assertIsNone(result)

    def test_stores_and_retrieves_content(self):
        key = "claude"
        content = "<feed>test content</feed>"

        self.cache.store(key, content)
        result = self.cache.get(key)

        self.assertEqual(result["content"], content)

    def test_stores_etag(self):
        key = "claude"
        content = "<feed>test</feed>"
        etag = '"abc123"'

        self.cache.store(key, content, etag=etag)
        result = self.cache.get(key)

        self.assertEqual(result["etag"], etag)

    def test_stores_timestamp(self):
        key = "claude"
        content = "<feed>test</feed>"

        self.cache.store(key, content)
        result = self.cache.get(key)

        self.assertIn("fetched_at", result)

    def test_is_fresh_within_max_age(self):
        key = "claude"
        self.cache.store(key, "<feed>test</feed>")

        # Should be fresh immediately after storing
        self.assertTrue(self.cache.is_fresh(key, max_age_seconds=60))

    def test_is_not_fresh_after_max_age(self):
        key = "claude"
        self.cache.store(key, "<feed>test</feed>")

        # Should not be fresh with 0 second max age
        self.assertFalse(self.cache.is_fresh(key, max_age_seconds=0))

    def test_is_not_fresh_when_not_cached(self):
        self.assertFalse(self.cache.is_fresh("missing", max_age_seconds=60))


if __name__ == "__main__":
    unittest.main()
