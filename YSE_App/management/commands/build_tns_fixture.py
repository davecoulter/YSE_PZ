"""
Build a reusable test database snapshot from TNS (2026f* transients).

Requires TNS API credentials in YSE_PZ/settings.ini or env (TNS_API_KEY).
Run with the Docker stack up so uploads hit add_transient:

  docker exec ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026f

Then export a static dump (from host):

  ./docker/scripts/build-test-fixture-db.sh export
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError

from YSE_App.data_ingest import tns_api_client
from YSE_App.models import Transient


def _import_tns_uploads():
    """Lazy import: TNS_uploads pulls many optional science deps."""
    from YSE_App.data_ingest.TNS_uploads import HAS_ASTRO_PROST, processTNS

    return processTNS, HAS_ASTRO_PROST


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
            help="Pan-STARRS score via get_ps_score (always attempted in getTNSData)",
        )
        parser.add_argument(
            "--with-prost",
            action="store_true",
            help="Run astro_prost host association (requires astro_prost package)",
        )
        parser.add_argument(
            "--with-spectra",
            action="store_true",
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            "--skip-spectra",
            action="store_true",
            help="Skip TNS spectrum download (default is to always fetch spectra when present)",
        )
        parser.add_argument(
            "--with-archival-flags",
            action="store_true",
            help="Probe MAST/Chandra/Spitzer for has_hst/has_chandra/has_spitzer (no image download)",
        )
        parser.add_argument(
            "--merge-manifest",
            action="store_true",
            help="Append/update manifest rows for ingested names; keep other 2026f* entries",
        )
        parser.add_argument(
            "--clobber",
            action="store_true",
            help="Replace existing photometry points on re-ingest (same MJD match window)",
        )
        parser.add_argument(
            "--full-ingest",
            action="store_true",
            help="Cron-style ingest: archival MAST/Chandra, ZTF/Antares, spectra (default is dashboard-only)",
        )
        parser.add_argument(
            "--max",
            type=int,
            default=None,
            help="Cap number of transients to ingest (default: all matches)",
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

        processTNS, has_astro_prost = _import_tns_uploads()
        tnsproc = processTNS()
        parser_cli = tnsproc.add_options(config=config)
        tns_opts, _ = parser_cli.parse_known_args([])

        tnsproc.tnsapi = tns_opts.tnsapi
        tnsproc.tnsapikey = os.environ.get("TNS_API_KEY") or tns_opts.tnsapikey
        tnsproc.tns_bot_id = tns_opts.tns_bot_id
        tnsproc.tns_bot_name = tns_opts.tns_bot_name
        marker_type = os.environ.get("TNS_MARKER_TYPE")
        if not marker_type and config.has_option("main", "tns_marker_type"):
            marker_type = config.get("main", "tns_marker_type")
        marker_type = (marker_type or "bot").strip()
        if str(tnsproc.tns_bot_id).startswith("<") or str(tnsproc.tns_bot_name).startswith("<"):
            raise CommandError(
                "TNS marker identity missing. Set [main] tns_bot_id and tns_bot_name "
                '(e.g. 151 and rfoley for tns_marker{"tns_id":151,"type":"user","name":"rfoley"})'
            )
        tnsproc.dblogin = os.environ.get("YSE_DB_LOGIN") or tns_opts.dblogin
        tnsproc.dbpassword = os.environ.get("YSE_DB_PASSWORD") or tns_opts.dbpassword
        tnsproc.dburl = options["dburl"] or tns_opts.dburl or "http://127.0.0.1:8000/api/"
        tnsproc.status = tns_opts.status
        tnsproc.noupdatestatus = True
        if options["with_prost"] and not has_astro_prost:
            raise CommandError(
                "--with-prost requires astro_prost (not installed in this container)"
            )
        tnsproc.tns_marker_type = marker_type
        dashboard_only = not options["full_ingest"]
        include_spectra = not options["skip_spectra"]
        if dashboard_only:
            tnsproc.fixture_skip_archival = not (
                options["full_ingest"] or options["with_archival_flags"]
            )
            tnsproc.fixture_skip_ztf_antares = True
            tnsproc.fixture_skip_spectra = not include_spectra
            tnsproc.fixture_skip_ps = not options["with_ps"]
            tnsproc.upload_batch_size = 1
            skip_parts = ["Antares ZTF"]
            if tnsproc.fixture_skip_archival:
                skip_parts.insert(0, "Chandra/HST/Spitzer probes")
            if options["skip_spectra"]:
                skip_parts.append("spectra")
            ingest_bits = "TNS metadata + photometry + E(B-V)"
            if include_spectra:
                ingest_bits += " + TNS spectra"
            if not tnsproc.fixture_skip_archival:
                ingest_bits += " + archival probes (has_hst, etc.)"
            self.stdout.write(
                f"Dashboard-only ingest: {ingest_bits}; "
                f"skipping {', '.join(skip_parts)}; uploading one transient per POST"
            )
        do_prost = options["with_prost"] and not dashboard_only
        tnsproc.redohost = do_prost
        tnsproc.clobber = options["clobber"]
        do_ebv = True

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
            marker_type,
        )
        if not names:
            raise CommandError(f"No TNS objects found for prefix {prefix!r}")

        total = len(names)
        if options["max"] is not None and options["max"] > 0:
            names = names[: options["max"]]
        self.stdout.write(
            f"Found {total} TNS match(es); ingesting {len(names)}: {', '.join(names[:10])}..."
        )
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
                marker_type,
            )
            if coords is None:
                self.stderr.write(f"Skipping {name}: no TNS coords")
                continue
            objs.append(name)
            ras.append(coords[0])
            decs.append(coords[1])
            time.sleep(1.0)

        if not objs:
            raise CommandError("No objects with coordinates to upload")

        if options["with_ps"]:
            self.stdout.write(
                "Note: Pan-STARRS scores are fetched per object in getTNSData "
                "(MAST Casjobs); --with-ps does not enable astro_prost."
            )
        tnsproc.GetAndUploadAllData(
            objs,
            ras,
            decs,
            doProst=do_prost,
            doEBV=do_ebv,
            doTNS=True,
        )

        manifest_path = Path(
            options["manifest"]
            or os.path.join(django_settings.BASE_DIR, "docker", "db_fixtures", "manifest.json")
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        new_rows = {
            r["name"]: r
            for r in Transient.objects.filter(name__in=objs).values(
                "id", "name", "slug", "ra", "dec", "status_id"
            )
        }
        if options["merge_manifest"] and manifest_path.is_file():
            existing = json.loads(manifest_path.read_text())
            merged = {t["name"]: t for t in existing.get("transients") or []}
            merged.update(new_rows)
            rows = sorted(merged.values(), key=lambda r: r["name"].lower())
            manifest_prefix = existing.get("prefix") or prefix
        else:
            rows = sorted(new_rows.values(), key=lambda r: r["name"].lower())
            manifest_prefix = prefix
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "prefix": manifest_prefix,
            "tns_count": len(rows),
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

    def _tns_names_for_prefix(self, api, api_key, bot_id, bot_name, prefix, marker_type="bot"):
        """Search TNS and keep names matching ^prefix + letters."""
        pattern = re.compile(rf"^{re.escape(prefix)}[a-zA-Z0-9]*$", re.IGNORECASE)
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
            return tns_api_client.search(
                api, search_obj, api_key, bot_id, bot_name, marker_type
            )

        response = self._tns_request_with_retry(do_search)
        if not response or not getattr(response, "text", None):
            return []
        data = tns_api_client.format_to_json(response.text)
        names = []
        for row in data.get("data", []):
            name = row.get("objname") or row.get("name")
            if name and pattern.match(name):
                names.append(name)
        return sorted(set(names))

    def _tns_coords(self, api, api_key, bot_id, bot_name, name, marker_type="bot"):
        payload = [("objname", name), ("photometry", "0"), ("spectra", "0")]

        def do_get():
            return tns_api_client.get(api, payload, api_key, bot_id, bot_name, marker_type)

        response = self._tns_request_with_retry(do_get)
        if not response or not getattr(response, "text", None):
            return None
        jd = tns_api_client.format_to_json(response.text)
        try:
            d = jd["data"]
            return d["ra"], d["dec"]
        except (KeyError, TypeError):
            return None
