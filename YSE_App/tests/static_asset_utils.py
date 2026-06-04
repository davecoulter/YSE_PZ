"""Helpers for asserting local static assets referenced in HTML."""

import re
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.staticfiles import finders

# Local /static/... URLs emitted by {% static %} (not third-party cutouts).
_LOCAL_STATIC_ATTR_RE = re.compile(
    r'(?:src|href)=["\'](/static/[^"\']+)["\']',
    re.IGNORECASE,
)

# Third-party sky cutouts; not collected under STATIC_ROOT (may time out offline).
_EXTERNAL_SKYVIEW_HOSTS = frozenset(
    {
        "skyservice.pha.jhu.edu",
        "skyserver.sdss3.org",
        "skyserver.sdss.org",
    }
)


def static_url_prefix():
    prefix = (settings.STATIC_URL or "/static/").strip()
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    if not prefix.endswith("/"):
        prefix += "/"
    return prefix


def local_static_paths_from_html(html):
    """Return deduplicated /static/... paths from src/href attributes."""
    seen = set()
    out = []
    for match in _LOCAL_STATIC_ATTR_RE.finditer(html):
        path = match.group(1)
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def static_relpath_from_url(static_url_path):
    """Map /static/YSE_App/foo.css -> YSE_App/foo.css."""
    prefix = static_url_prefix()
    if static_url_path.startswith(prefix):
        return static_url_path[len(prefix) :].lstrip("/")
    if static_url_path.startswith("/static/"):
        return static_url_path[len("/static/") :]
    return static_url_path.lstrip("/")


def static_asset_available(relative_path):
    """True if asset exists in app static dirs or under STATIC_ROOT."""
    if finders.find(relative_path):
        return True
    root = Path(settings.STATIC_ROOT)
    return (root / relative_path).is_file()


def external_skyview_urls_from_html(html):
    urls = []
    for match in re.finditer(r'(?:src|href)=["\'](https?://[^"\']+)["\']', html, re.I):
        host = urlparse(match.group(1)).hostname or ""
        if host in _EXTERNAL_SKYVIEW_HOSTS:
            urls.append(match.group(1))
    return urls
