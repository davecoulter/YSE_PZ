"""
Build a reusable test database snapshot from TNS (2026f* transients).

Requires TNS API credentials in YSE_PZ/settings.ini or env (TNS_API_KEY).
Run with the Docker stack up so uploads hit add_transient:

  docker exec ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026f

Then export a static dump (from host):

  ./docker/scripts/build-test-fixture-db.sh export
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError

from YSE_App.data_ingest.TNS_uploads import format_to_json, get, processTNS, search
from YSE_App.models import Transient


class Command(BaseCommand):
    help = "Ingest TNS transients matching a name prefix into the DB and write a fixture manifest."

    def add_arguments(self, parser):
        parser.add_argument(
            "--prefix",
            default="2026f",
            help="Transient name prefix (default: 2026f)",
        )
        parser.add_argument(
            "--settingsfile",
            default=None,
            help="Path to settings.ini (default: PROJECT_DIR/settings.ini)",
        )
        parser.add_argument(
            "--dburl",
            default=None,
            help="add_transient base URL (default: http://127.0.0.1:8000/api/)",
        )
        parser.add_argument(
            "--with-ps",
            action="store_true",
            help="Fetch Pan-STARRS star/galaxy scores (needs MAST Casjobs env in TNS_uploads)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List TNS matches only; do not upload",
        )
        parser.add_argument(
            "--manifest",
            default=None,
            help="Manifest JSON path (default: docker/db_fixtures/manifest.json)",
        )

    def handle(self, *args, **options):
        prefix = options["prefix"].strip()
        if not prefix:
            raise CommandError("--prefix must be non-empty")

        settingsfile = options["settingsfile"] or os.path.join(
            django_settings.PROJECT_DIR, "settings.ini"
        )
        if not os.path.isfile(settingsfile):
            raise CommandError(f"settings.ini not found: {settingsfile}")

        import configparser

        config = configparser.ConfigParser()
        config.read(settingsfile)

        tnsproc = processTNS()
        parser_cli = tnsproc.add_options(config=config)
        tns_opts, _ = parser_cli.parse_known_args([])

        tnsproc.tnsapi = tns_opts.tnsapi
        tnsproc.tnsapikey = os.environ.get("TNS_API_KEY") or tns_opts.tnsapikey
        tnsproc.tns_bot_id = tns_opts.tns_bot_id
        tnsproc.tns_bot_name = tns_opts.tns_bot_name
        tnsproc.dblogin = tns_opts.dblogin
        tnsproc.dbpassword = tns_opts.dbpassword
        tnsproc.dburl = options["dburl"] or tns_opts.dburl or "http://127.0.0.1:8000/api/"
        tnsproc.status = tns_opts.status
        tnsproc.noupdatestatus = True
        tnsproc.redohost = options["with_ps"]
        tnsproc.clobber = False

        if not tnsproc.tnsapikey or str(tnsproc.tnsapikey).startswith("<"):
            raise CommandError(
                "TNS API key missing. Set TNS_API_KEY env or [main] tnsapikey in settings.ini"
            )

        names = self._tns_names_for_prefix(
            tnsproc.tnsapi,
            tnsproc.tnsapikey,
            tnsproc.tns_bot_id,
            tnsproc.tns_bot_name,
            prefix,
        )
        if not names:
            raise CommandError(f"No TNS objects found for prefix {prefix!r}")

        self.stdout.write(f"Found {len(names)} TNS object(s): {', '.join(names[:10])}...")
        if options["dry_run"]:
            return

        objs, ras, decs = [], [], []
        for name in names:
            coords = self._tns_coords(
                tnsproc.tnsapi,
                tnsproc.tnsapikey,
                tnsproc.tns_bot_id,
                tnsproc.tns_bot_name,
                name,
            )
            if coords is None:
                self.stderr.write(f"Skipping {name}: no TNS coords")
                continue
            objs.append(name)
            ras.append(coords[0])
            decs.append(coords[1])
            time.sleep(0.5)

        if not objs:
            raise CommandError("No objects with coordinates to upload")

        tnsproc.GetAndUploadAllData(
            objs,
            ras,
            decs,
            doProst=options["with_ps"],
            doEBV=options["with_ps"],
            doTNS=True,
        )

        manifest_path = Path(
            options["manifest"]
            or os.path.join(django_settings.BASE_DIR, "docker", "db_fixtures", "manifest.json")
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        rows = list(
            Transient.objects.filter(name__in=objs).values(
                "id", "name", "slug", "ra", "dec", "status_id"
            )
        )
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "prefix": prefix,
            "tns_count": len(objs),
            "transients": rows,
        }
        manifest_path.write_text(json.dumps(payload, indent=2) + "\n")
        self.stdout.write(self.style.SUCCESS(f"Wrote manifest: {manifest_path}"))
        self.stdout.write(
            "Export static DB: ./docker/scripts/build-test-fixture-db.sh export"
        )

    def _tns_request_with_retry(self, request_fn, max_tries=5):
        for attempt in range(max_tries):
            response = request_fn()
            if getattr(response, "status_code", None) == 429:
                self.stdout.write("TNS rate limit; sleeping 60s...")
                time.sleep(60)
                continue
            return response
        return response

    def _tns_names_for_prefix(self, api, api_key, bot_id, bot_name, prefix):
        """Search TNS and keep names matching ^prefix + letters."""
        pattern = re.compile(rf"^{re.escape(prefix)}[A-Za-z]+$")
        search_obj = [
            ("ra", ""),
            ("dec", ""),
            ("radius", ""),
            ("units", ""),
            ("objname", prefix),
            ("internal_name", ""),
            ("public_timestamp", ""),
        ]

        def do_search():
            return search(api, search_obj, api_key, bot_id, bot_name)

        response = self._tns_request_with_retry(do_search)
        if not response or not getattr(response, "text", None):
            return []
        data = format_to_json(response.text)
        names = []
        for row in data.get("data", []):
            name = row.get("objname") or row.get("name")
            if name and pattern.match(name):
                names.append(name)
        return sorted(set(names))

    def _tns_coords(self, api, api_key, bot_id, bot_name, name):
        payload = [("objname", name), ("photometry", "0"), ("spectra", "0")]

        def do_get():
            return get(api, payload, api_key, bot_id, bot_name)

        response = self._tns_request_with_retry(do_get)
        if not response or not getattr(response, "text", None):
            return None
        jd = format_to_json(response.text)
        try:
            d = jd["data"]
            return d["ra"], d["dec"]
        except (KeyError, TypeError):
            return None
