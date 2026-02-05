"""Tests for incident formatting."""

import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import Incident, is_likely_resolved, is_likely_active, format_incidents


class TestIsLikelyResolved(unittest.TestCase):
    """Test status pattern matching for resolved incidents."""

    def test_resolved_is_resolved(self):
        self.assertTrue(is_likely_resolved(Incident(title="", link="", status="Resolved")))

    def test_fixed_is_resolved(self):
        self.assertTrue(is_likely_resolved(Incident(title="", link="", status="Fixed")))

    def test_completed_is_resolved(self):
        self.assertTrue(is_likely_resolved(Incident(title="", link="", status="Completed")))

    def test_investigating_is_not_resolved(self):
        self.assertFalse(is_likely_resolved(Incident(title="", link="", status="Investigating")))

    def test_identified_is_not_resolved(self):
        self.assertFalse(is_likely_resolved(Incident(title="", link="", status="Identified")))

    def test_monitoring_is_not_resolved(self):
        self.assertFalse(is_likely_resolved(Incident(title="", link="", status="Monitoring")))

    def test_case_insensitive(self):
        self.assertTrue(is_likely_resolved(Incident(title="", link="", status="RESOLVED")))
        self.assertTrue(is_likely_resolved(Incident(title="", link="", status="resolved")))

    def test_back_to_normal_is_resolved(self):
        self.assertTrue(is_likely_resolved(Incident(title="", link="", status="Back to normal")))

    def test_fully_operational_is_resolved(self):
        self.assertTrue(is_likely_resolved(Incident(title="", link="", status="Fully operational")))


class TestIsLikelyActive(unittest.TestCase):
    """Test active incident detection (recent AND not resolved)."""

    def _recent_timestamp(self):
        """Return a timestamp from 1 hour ago."""
        return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    def _old_timestamp(self):
        """Return a timestamp from 48 hours ago."""
        return (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()

    def test_recent_investigating_is_active(self):
        incident = Incident(
            title="Test",
            link="",
            status="Investigating",
            published=self._recent_timestamp()
        )
        self.assertTrue(is_likely_active(incident))

    def test_recent_resolved_is_not_active(self):
        incident = Incident(
            title="Test",
            link="",
            status="Resolved",
            published=self._recent_timestamp()
        )
        self.assertFalse(is_likely_active(incident))

    def test_old_investigating_is_not_active(self):
        incident = Incident(
            title="Test",
            link="",
            status="Investigating",
            published=self._old_timestamp()
        )
        self.assertFalse(is_likely_active(incident))

    def test_no_timestamp_is_not_active(self):
        incident = Incident(title="Test", link="", status="Investigating")
        self.assertFalse(is_likely_active(incident))


class TestFormatIncidents(unittest.TestCase):
    def _recent_timestamp(self):
        """Return a timestamp from 1 hour ago."""
        return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    def test_shows_no_active_when_all_resolved(self):
        incidents = [Incident(
            title="Test",
            link="http://example.com",
            status="Resolved",
            published=self._recent_timestamp()
        )]
        output = format_incidents("Test Service", incidents)
        self.assertIn("No active incidents", output)

    def test_shows_active_section_when_active(self):
        incidents = [Incident(
            title="Ongoing Issue",
            link="http://example.com",
            status="Investigating",
            published=self._recent_timestamp()
        )]
        output = format_incidents("Test Service", incidents)
        self.assertIn("ACTIVE INCIDENTS", output)
        self.assertIn("Ongoing Issue", output)

    def test_shows_no_active_when_old_incident(self):
        """Old unresolved incidents should not show as active."""
        old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        incidents = [Incident(
            title="Old Issue",
            link="http://example.com",
            status="Investigating",
            published=old_timestamp
        )]
        output = format_incidents("Test Service", incidents)
        self.assertIn("No active incidents", output)


if __name__ == "__main__":
    unittest.main()
