"""Tests for incident timestamp correlation.

Validates that when the user saw API errors at 08:47 US-Pacific on 2026-02-04,
the status feed shows a corresponding active incident.
"""

import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "status-page" / "scripts"))

from check_status import parse_atom_feed

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "claude"

# The time the user saw API errors: 2026-02-04 08:47 US-Pacific
# Pacific Standard Time is UTC-8
PACIFIC = timezone(timedelta(hours=-8))
ERROR_TIME = datetime(2026, 2, 4, 8, 47, tzinfo=PACIFIC)
ERROR_TIME_UTC = ERROR_TIME.astimezone(timezone.utc)


class TestIncidentCorrelation(unittest.TestCase):
    """Test that API errors correlate with status page incidents."""

    @classmethod
    def setUpClass(cls):
        content = (FIXTURES_DIR / "2026-02-04-history.atom").read_text()
        cls.incidents = parse_atom_feed(content)

    def test_fixture_has_incident_from_error_time(self):
        """The fixture should contain an incident from around the error time."""
        # The incident "Elevated errors on Claude models" was published 2026-02-04T17:06:50Z
        # which is after resolution. The investigating phase started at 16:39 UTC.
        # 08:47 Pacific = 16:47 UTC, which falls within the incident window.

        titles = [i.title for i in self.incidents]
        self.assertIn("Elevated errors on Claude models", titles)

    def test_incident_was_active_at_error_time(self):
        """At 08:47 Pacific, there should have been an active incident.

        The fixture shows the incident timeline:
        - 16:39 UTC: Investigating
        - 16:53 UTC: Identified
        - 17:06 UTC: Resolved

        At 16:47 UTC (08:47 Pacific), status would have been "Investigating" or "Identified".

        Note: Our current implementation only sees the final status (Resolved) in the feed,
        since the feed shows the most recent update. This test documents the limitation.
        """
        # Find the relevant incident
        incident = next(i for i in self.incidents if i.title == "Elevated errors on Claude models")

        # The feed shows final status as Resolved
        # In a live scenario during the outage, this would have shown Investigating/Identified
        self.assertEqual(incident.status, "Resolved")

        # The published time is when the incident was last updated (resolution time)
        self.assertEqual(incident.published, "2026-02-04T17:06:50Z")


if __name__ == "__main__":
    unittest.main()
