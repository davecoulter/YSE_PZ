"""
Optional smoke tests against a running Docker stack (nginx on :8080).

Set YSE_LIVE_SMOKE=1 and ensure the stack is up with collectstatic run:

  ./docker/scripts/yse-docker.sh collectstatic
  YSE_LIVE_SMOKE=1 python3 manage.py test YSE_App.tests.test_live_static_smoke -v2
"""

import os
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LIVE_BASE = os.environ.get("YSE_LIVE_URL", "http://127.0.0.1:8080").rstrip("/")
THEME_PATH = "/static/YSE_App/yse-theme.css"


@unittest.skipUnless(
    os.environ.get("YSE_LIVE_SMOKE") == "1",
    "Set YSE_LIVE_SMOKE=1 to hit the running nginx stack",
)
class LiveDockerStaticSmokeTests(unittest.TestCase):
    def test_yse_theme_css_served_by_nginx(self):
        url = f"{LIVE_BASE}{THEME_PATH}"
        try:
            with urlopen(Request(url), timeout=10) as resp:
                status = resp.status
                body = resp.read(200)
        except HTTPError as exc:
            self.fail(f"{url} returned HTTP {exc.code} (run collectstatic)")
        except URLError as exc:
            self.skipTest(f"Stack not reachable at {LIVE_BASE}: {exc}")
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b"/*") or b"--yse" in body or b":root" in body)
