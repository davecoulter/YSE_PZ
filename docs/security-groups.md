# Group-based access control

YSE uses Django **collaboration groups** (`auth.Group`) on photometry, spectra, and telescope resources. Survey `ObservationGroup` on transients is metadata only.

## Rules

- **Empty `groups` M2M** on photometry/spectra/resources: visible to all logged-in users (unchanged).
- **Every user** is a member of the `Public` collaboration group (signal on user create + `ensure_users_in_public_group` for backfill).
- **New transient comments**: private by default (`Log.is_public=False` with `Log.groups` set to shared collaboration groups). Opt-in `is_public=True` for all collaborators who can open the transient.
- **Legacy comments** (before migration `0005_log_visibility`): `is_public=True`, no groups — unchanged visibility.
- **Follow-up requests** (`TransientFollowup`): default **public** (`is_public=True`). Restrict with `is_public=False` and optional `groups` M2M; `requested_by` is set on create.

## Code

- [`YSE_App/services/visibility.py`](../YSE_App/services/visibility.py) — shared helpers (`filter_transient_followups_for_user`, etc.)
- [`YSE_App/services/comments.py`](../YSE_App/services/comments.py) — comment create/list filtering

## SQL Explorer

Staff-only (`EXPLORER_PERMISSION_VIEW` / `CHANGE` in settings). Dashboard and canvas SQL results are post-filtered with `filter_transients_by_user_access`.

## Manual test matrix

Seed demo users and a labeled transient for browser testing:

```bash
docker exec ysepz_web_container python3 manage.py seed_security_test_matrix
```

| User | Password | Groups | Expected LC magnitudes |
|------|----------|--------|------------------------|
| `sec_user_ab` | `sec-test-pass` | A, B | 0, 1, 2, 5, 6, 7 |
| `sec_user_ac` | `sec-test-pass` | A, C | 0, 1, 3, 5, 6, 7 |
| `sec_user_b` | `sec-test-pass` | B | 0, 2, 5, 7 |
| `sec_user_d` | `sec-test-pass` | D | 0, 4 |

Transient **`secvis-matrix`**: each photometry point’s magnitude equals its test ID (0 = public, 1 = group A only, …, 7 = groups B+C). Open `/transient_detail/secvis-matrix/` after logging in.

Fixture code: [`YSE_App/tests/fixtures_security_matrix.py`](../YSE_App/tests/fixtures_security_matrix.py). Automated checks: [`test_security_matrix.py`](../YSE_App/tests/test_security_matrix.py).

### TNS ingest

TNS photometry and spectra are tagged with the `Public` collaboration group on import
(`YSE_App/common/collaboration_groups.py`, `TNS_uploads.getTNSPhotometry` / `getTNSSpectra`).

Backfill legacy ungrouped TNS rows on a server snapshot:

```bash
docker exec ysepz_web_container python3 manage.py mark_tns_imports_public --dry-run
docker exec ysepz_web_container python3 manage.py mark_tns_imports_public
```

Tests: `YSE_App.tests.test_tns_import_groups`.

### v1 create-time audience UI

Comments (Summary tab) and follow-up requests expose **Who can see this?** controls at submit time:

- **Comments:** default private to collaboration groups you share on this transient; opt-in checkbox “Visible to all YSE users who can open this transient”. When you belong to multiple groups, checkboxes list which groups may read the comment.
- **Follow-ups:** default public (checkbox checked); uncheck to restrict to selected collaboration groups.

Automated tests: `YSE_App.tests.test_audience_ui_v1`.

#### Manual checks (audience UI)

1. Seed matrix: `python3 manage.py seed_security_test_matrix`
2. As `sec_user_ab` / `sec-test-pass`, open `/transient_detail/secvis-matrix/`
3. **Comment — default private:** post “test private AB” with no audience checkbox. Log in as `sec_user_d` — comment must **not** appear (no shared group). Log in as `sec_user_ab` — comment **must** appear. Log in as `sec_user_ac` — **may** appear (shares group A with the audience).
4. **Comment — public:** as `sec_user_ab`, check “Visible to all YSE users…”, post “test public”. As `sec_user_ac`, comment **must** appear.
5. **Comment — group B only:** as `sec_user_ab`, uncheck public, select only `sec-group-b`, post “test B only”. As `sec_user_b` — visible; as `sec_user_ac` — **not** visible.
6. **Follow-up — default public:** as `sec_user_ab`, add follow-up with public checked (default). As `sec_user_ac`, follow-up row **must** appear on Follow-up tab.
7. **Follow-up — restricted:** uncheck public, select `sec-group-b` only, submit. As `sec_user_b` — visible; as `sec_user_ac` — **not** visible.

Backfill existing users on a server snapshot:

```bash
docker exec ysepz_web_container python3 manage.py ensure_users_in_public_group --dry-run
docker exec ysepz_web_container python3 manage.py ensure_users_in_public_group
```

### Production group names (regression)

Tests use the same collaboration group names as the server (`Public`, `YSE`, `UCSC`, `LCOGT`, …) — see [`fixtures_production_groups.py`](../YSE_App/tests/fixtures_production_groups.py) and [`test_production_group_access.py`](../YSE_App/tests/test_production_group_access.py).

```bash
# Always run (synthetic transient prodgrp-vis-test)
docker exec ysepz_web_container python3 manage.py test \
  YSE_App.tests.test_production_group_access.ProductionGroupPatternTests --keepdb -v2

# After importing a production DB snapshot (validates on the **default** DB, not test DB):
docker exec ysepz_web_container python3 manage.py verify_production_group_access
```

Plot HTML cache keys use `group_access_plot_cache_token()` — a hash of sorted group names, not user id.

## Remaining ([#102](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/102))

- Per-group Slack ([#100](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/100))
- DRF hardening (`TransientViewSet`, export headers, notifications)
