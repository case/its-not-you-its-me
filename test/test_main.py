"""Tests for main() function."""

import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

import check_status

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "claude"


class TestMain(unittest.TestCase):
    def setUp(self):
        self.held_stdout = StringIO()
        self.held_stderr = StringIO()

    @patch("check_status.fetch_feed")
    @patch("check_status.get_default_cache_dir")
    def test_main_outputs_status(self, mock_cache_dir, mock_fetch):
        # Setup mocks
        mock_cache_dir.return_value = Path(tempfile.mkdtemp())
        mock_fetch.return_value = (FIXTURES_DIR / "2026-02-04-history.atom").read_text()

        # Run main with captured stdout
        with patch.object(sys, "argv", ["check_status.py", "claude"]):
            with patch.object(sys, "stdout", self.held_stdout):
                check_status.main()

        output = self.held_stdout.getvalue()
        self.assertIn("Claude Status", output)
        self.assertIn("Elevated errors on Claude models", output)

    @patch("check_status.fetch_feed")
    @patch("check_status.get_default_cache_dir")
    def test_main_shows_no_active_when_resolved(self, mock_cache_dir, mock_fetch):
        mock_cache_dir.return_value = Path(tempfile.mkdtemp())
        mock_fetch.return_value = (FIXTURES_DIR / "2026-02-04-history.atom").read_text()

        with patch.object(sys, "argv", ["check_status.py", "claude"]):
            with patch.object(sys, "stdout", self.held_stdout):
                check_status.main()

        output = self.held_stdout.getvalue()
        self.assertIn("No active incidents", output)

    def test_main_exits_on_unknown_service(self):
        with patch.object(sys, "argv", ["check_status.py", "unknown-service"]):
            with patch.object(sys, "stdout", self.held_stdout):
                with self.assertRaises(SystemExit) as ctx:
                    check_status.main()
                self.assertEqual(ctx.exception.code, 1)

        output = self.held_stdout.getvalue()
        self.assertIn("Unknown service", output)

    def test_main_exits_on_no_args(self):
        with patch.object(sys, "argv", ["check_status.py"]):
            with patch.object(sys, "stdout", self.held_stdout):
                with self.assertRaises(SystemExit) as ctx:
                    check_status.main()
                self.assertEqual(ctx.exception.code, 1)

        output = self.held_stdout.getvalue()
        self.assertIn("Usage:", output)

    @patch("check_status.fetch_feed")
    @patch("check_status.get_default_cache_dir")
    def test_main_handles_alias(self, mock_cache_dir, mock_fetch):
        mock_cache_dir.return_value = Path(tempfile.mkdtemp())
        mock_fetch.return_value = (FIXTURES_DIR / "2026-02-04-history.atom").read_text()

        # Use alias "anthropic" instead of "claude"
        with patch.object(sys, "argv", ["check_status.py", "anthropic"]):
            with patch.object(sys, "stdout", self.held_stdout):
                check_status.main()

        output = self.held_stdout.getvalue()
        self.assertIn("Claude Status", output)


if __name__ == "__main__":
    unittest.main()
