#!/usr/bin/env python3
"""Check service status pages for incidents."""

import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path

import tomllib

__all__ = [
    "FeedCache",
    "FeedParseError",
    "FeedTooLargeError",
    "Incident",
    "MAX_FEED_ENTRIES",
    "MAX_FEED_SIZE_BYTES",
    "extract_status_from_html",
    "fetch_feed",
    "find_service",
    "format_incidents",
    "is_likely_active",
    "is_likely_resolved",
    "is_recent_incident",
    "load_services",
    "parse_atom_feed",
    "parse_rss_feed",
    "parse_timestamp",
]


@dataclass
class Incident:
    """Represents a status page incident."""

    title: str
    link: str
    status: str
    published: str = ""


class FeedCache:
    """Simple file-based cache for feed content."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _content_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.xml"

    def _meta_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> dict | None:
        """Get cached content and metadata for a service key."""
        content_path = self._content_path(key)
        meta_path = self._meta_path(key)

        if not content_path.exists() or not meta_path.exists():
            return None

        content = content_path.read_text()
        meta = json.loads(meta_path.read_text())

        return {
            "content": content,
            "etag": meta.get("etag"),
            "fetched_at": meta.get("fetched_at"),
        }

    def get_if_fresh(self, key: str, max_age_seconds: int) -> dict | None:
        """Get cached content only if it's still fresh. Returns None if stale or missing."""
        cached = self.get(key)
        if not cached:
            return None

        fetched_at = cached.get("fetched_at", 0)
        if (time.time() - fetched_at) >= max_age_seconds:
            return None

        return cached

    def store(self, key: str, content: str, etag: str | None = None):
        """Store content and metadata for a service key."""
        content_path = self._content_path(key)
        meta_path = self._meta_path(key)

        content_path.write_text(content)
        meta_path.write_text(
            json.dumps(
                {
                    "etag": etag,
                    "fetched_at": time.time(),
                }
            )
        )

    def is_fresh(self, key: str, max_age_seconds: int) -> bool:
        """Check if cached content is still fresh."""
        meta_path = self._meta_path(key)

        if not meta_path.exists():
            return False

        meta = json.loads(meta_path.read_text())
        fetched_at = meta.get("fetched_at", 0)

        return (time.time() - fetched_at) < max_age_seconds


def extract_status_from_html(html_content: str) -> str:
    """Extract the most recent status from HTML content.

    Status markers appear as <strong>Status</strong> in the content.
    The first one is the most recent update.

    Note: The raw feed contains HTML entities like &lt;strong&gt;, but
    xml.etree.ElementTree automatically unescapes these when parsing,
    so we match against literal <strong> tags here.
    """
    match = re.search(r"<strong>(\w+)</strong>", html_content)
    if match:
        return match.group(1)
    return "Unknown"


class FeedParseError(Exception):
    """Raised when a feed cannot be parsed."""

    pass


# Limit entries to prevent resource exhaustion from malicious feeds
MAX_FEED_ENTRIES = 100


def parse_atom_feed(
    content: str, max_entries: int = MAX_FEED_ENTRIES
) -> list[Incident]:
    """Parse an Atom feed and return a list of incidents.

    Raises:
        FeedParseError: If the content is not valid XML or not a valid Atom feed.
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise FeedParseError(f"Invalid XML: {e}") from e

    ns = {"atom": "http://www.w3.org/2005/Atom"}

    incidents = []
    for entry in root.findall("atom:entry", ns):
        if len(incidents) >= max_entries:
            break

        title = entry.find("atom:title", ns)
        link = entry.find("atom:link[@rel='alternate']", ns)
        published = entry.find("atom:published", ns)
        content_elem = entry.find("atom:content", ns)

        incident = Incident(
            title=(title.text or "") if title is not None else "",
            link=(link.get("href") or "") if link is not None else "",
            published=(published.text or "") if published is not None else "",
            status=extract_status_from_html(content_elem.text or "")
            if content_elem is not None
            else "Unknown",
        )
        incidents.append(incident)

    return incidents


def parse_rss_feed(content: str, max_entries: int = MAX_FEED_ENTRIES) -> list[Incident]:
    """Parse an RSS feed and return a list of incidents.

    Raises:
        FeedParseError: If the content is not valid XML or not a valid RSS feed.
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise FeedParseError(f"Invalid XML: {e}") from e

    incidents = []
    for item in root.findall(".//item"):
        if len(incidents) >= max_entries:
            break

        title = item.find("title")
        link = item.find("link")
        description = item.find("description")
        pub_date = item.find("pubDate")

        incident = Incident(
            title=(title.text or "") if title is not None else "",
            link=(link.text or "") if link is not None else "",
            published=(pub_date.text or "") if pub_date is not None else "",
            status=extract_status_from_html(description.text or "")
            if description is not None
            else "Unknown",
        )
        incidents.append(incident)

    return incidents


@lru_cache(maxsize=8)
def _load_services_cached(path_str: str) -> dict:
    """Internal cached loader using string path for hashability."""
    with open(path_str, "rb") as f:
        return tomllib.load(f)


def load_services(path: Path) -> dict:
    """Load service configuration from a TOML file. Results are cached."""
    return _load_services_cached(str(path))


def find_service(services: dict, query: str) -> tuple[str, dict] | None:
    """Find a service by key or alias. Returns (key, service) or None."""
    query = query.lower()

    # Check direct key match
    if query in services:
        return (query, services[query])

    # Check aliases
    for key, service in services.items():
        if query in service.get("aliases", []):
            return (key, service)

    return None


class FeedTooLargeError(Exception):
    """Raised when a feed exceeds the maximum allowed size."""

    pass


# 1MB max - status feeds are typically <100KB
MAX_FEED_SIZE_BYTES = 1024 * 1024


def fetch_feed(
    url: str,
    cache: FeedCache | None = None,
    cache_key: str | None = None,
    max_age_seconds: int = 60,
    max_size_bytes: int = MAX_FEED_SIZE_BYTES,
) -> str:
    """Fetch feed content from a URL, using cache if available.

    Raises:
        FeedTooLargeError: If the response exceeds max_size_bytes.
    """
    key = cache_key or url

    # Check if we have fresh cached content
    if cache:
        fresh = cache.get_if_fresh(key, max_age_seconds)
        if fresh:
            return fresh["content"]

    # Build request headers
    headers = {"User-Agent": "status-page-checker/1.0"}

    # Add If-None-Match header if we have a cached ETag
    cached_etag = None
    if cache:
        cached = cache.get(key)
        if cached and cached.get("etag"):
            cached_etag = cached["etag"]
            headers["If-None-Match"] = cached_etag

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            # Check Content-Length header first (if provided)
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_size_bytes:
                raise FeedTooLargeError(
                    f"Feed size {content_length} exceeds limit of {max_size_bytes} bytes"
                )

            # Read with size limit
            content_bytes = response.read(max_size_bytes + 1)
            if len(content_bytes) > max_size_bytes:
                raise FeedTooLargeError(f"Feed exceeds limit of {max_size_bytes} bytes")

            content = content_bytes.decode("utf-8")
            etag = response.headers.get("ETag")

            # Store in cache
            if cache:
                cache.store(key, content, etag=etag)

            return content

    except urllib.error.HTTPError as e:
        # 304 Not Modified - use cached content
        if e.code == 304 and cache:
            cached = cache.get(key)
            if cached:
                # Update the timestamp so it stays fresh
                cache.store(key, cached["content"], etag=cached_etag)
                return cached["content"]
        raise


def parse_timestamp(timestamp: str) -> datetime | None:
    """Parse a timestamp from either ISO 8601 (Atom) or RFC 822 (RSS) format.

    Returns None if parsing fails.
    """
    if not timestamp:
        return None

    # Try ISO 8601 format (Atom feeds): 2026-02-04T17:06:50Z
    try:
        # Handle Z suffix
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp)
    except ValueError:
        pass

    # Try RFC 822 format (RSS feeds): Wed, 04 Feb 2026 17:06:50 +0000
    try:
        return parsedate_to_datetime(timestamp)
    except (ValueError, TypeError):
        pass

    return None


def is_recent_incident(incident: Incident, hours: int = 4) -> bool:
    """Check if incident was updated within the last N hours."""
    parsed = parse_timestamp(incident.published)
    if not parsed:
        return False

    now = datetime.now(timezone.utc)
    age = now - parsed
    return age.total_seconds() < (hours * 3600)


# Common words/phrases indicating an incident is resolved (case-insensitive)
RESOLVED_PATTERNS = [
    "resolved",
    "fixed",
    "closed",
    "completed",
    "recovered",
    "restored",
    "back to normal",
    "fully operational",
]


def is_likely_resolved(incident: Incident) -> bool:
    """Check if status suggests the incident is resolved.

    Uses pattern matching to work across different status page providers.
    """
    status = incident.status.lower()
    return any(pattern in status for pattern in RESOLVED_PATTERNS)


def is_likely_active(incident: Incident, recent_hours: int = 4) -> bool:
    """Check if an incident is likely currently active.

    An incident is considered active if:
    1. It was updated recently (within recent_hours), AND
    2. Its status doesn't suggest it's resolved
    """
    return is_recent_incident(incident, recent_hours) and not is_likely_resolved(
        incident
    )


def format_incidents(
    service_name: str, incidents: list[Incident], limit: int = 5
) -> str:
    """Format incidents for human-readable output."""
    lines = [f"# {service_name} Status", ""]

    if not incidents:
        lines.append("No recent incidents.")
        return "\n".join(lines)

    # Check for active incidents
    active = [i for i in incidents if is_likely_active(i)]

    if active:
        lines.append("## ACTIVE INCIDENTS")
        lines.append("")
        for incident in active:
            lines.append(f">>> [{incident.status}] {incident.title}")
            if incident.link:
                lines.append(f"    {incident.link}")
        lines.append("")
        lines.append("## Recent History")
        lines.append("")
    else:
        lines.append("No active incidents.")
        # Show when the last incident was
        if incidents:
            last_incident = incidents[0]
            last_time = parse_timestamp(last_incident.published)
            if last_time:
                utc_str = last_time.strftime("%Y-%m-%d %H:%M UTC")
                local_time = last_time.astimezone()
                local_str = local_time.strftime("%H:%M %Z")
                lines.append(f"The last incident: {utc_str} ({local_str})")
        lines.append("")
        lines.append("## Recent History")
        lines.append("")

    for incident in incidents[:limit]:
        lines.append(f"- [{incident.status}] {incident.title}")
        if incident.link:
            lines.append(f"  {incident.link}")

    return "\n".join(lines)


def get_default_cache_dir() -> Path:
    """Get the default cache directory."""
    return Path.home() / ".cache" / "status-page"


DEFAULT_SERVICE = "claude"


def main():
    """Main entry point."""
    query = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_SERVICE

    # Load services config from same directory as script
    script_dir = Path(__file__).parent.parent
    services_path = script_dir / "services.toml"

    services = load_services(services_path)
    result = find_service(services, query)

    if not result:
        print(f"Unknown service: {query}")
        print(f"Available services: {', '.join(services.keys())}")
        sys.exit(1)

    service_key, service = result

    # Initialize cache
    cache = FeedCache(get_default_cache_dir())

    # Fetch and parse feed
    feed_url = service["feed"]
    feed_type = service.get("feed_type", "atom")

    try:
        content = fetch_feed(
            feed_url, cache=cache, cache_key=service_key, max_age_seconds=60
        )
    except urllib.error.URLError as e:
        print(f"Error fetching {service['name']} status: {e}")
        sys.exit(1)

    try:
        if feed_type == "atom":
            incidents = parse_atom_feed(content)
        else:
            incidents = parse_rss_feed(content)
    except FeedParseError as e:
        print(f"Error parsing {service['name']} feed: {e}")
        sys.exit(1)

    # Output results
    print(format_incidents(service["name"], incidents))


if __name__ == "__main__":
    main()
