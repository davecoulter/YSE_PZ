# Group-based access control

YSE uses Django **collaboration groups** (`auth.Group`) on photometry, spectra, and telescope resources. Survey `ObservationGroup` on transients is metadata only.

## Rules

- **Empty `groups` M2M** on photometry/spectra/resources: visible to all logged-in users (unchanged).
- **Every user** is a member of the `Public` collaboration group (signal on user create + `ensure_users_in_public_group` for backfill).
- **New transient comments**: private by default (`Log.is_public=False` with `Log.groups` set to shared collaboration groups). Opt-in `is_public=True` for all collaborators who can open the transient.
- **Legacy comments** (before migration `0005_log_visibility`): `is_public=True`, no groups — unchanged visibility.
- **Follow-up requests** (`TransientFollowup`): audience is set via collaboration groups at create time (`is_public=False` on new rows). Legacy rows with `is_public=True` and no groups remain visible to Public group members who can also see the linked observing resource. Restricted follow-ups require group membership **and** visibility of the linked classical/ToO/queued resource.

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

- **Comments:** default private to collaboration groups you share on this transient (group checkboxes pre-selected); opt-in checkbox “Visible to all YSE users who can open this transient”. Uncheck public and all groups to keep a comment visible only to you.
- **Follow-ups:** select collaboration groups that can see the linked observing resource (default: all eligible groups checked). Check **Public** to share with everyone in the Public collaboration group — only enabled when the observing resource is itself public (no group restrictions). At least one eligible group is required. Creator-only requests (no groups) are allowed only for creator-only observing resources (not yet in production).

Automated tests: `YSE_App.tests.test_audience_ui_v1`.

#### Manual checks (audience UI)

1. Seed matrix: `python3 manage.py seed_security_test_matrix`
2. As `sec_user_ab` / `sec-test-pass`, open `/transient_detail/secvis-matrix/`
3. **Comment — default private:** as `sec_user_ab`, leave public unchecked and keep default group checkboxes selected, post “test private AB”. Log in as `sec_user_d` — comment must **not** appear. Log in as `sec_user_ab` — comment **must** appear. Log in as `sec_user_ac` — **may** appear (shares group A with the audience).
4. **Comment — creator only:** as `sec_user_b`, uncheck public and uncheck `sec-group-b`, post “test creator only”. As `sec_user_b` — visible; as `sec_user_ab` — **not** visible.
5. **Comment — public:** as `sec_user_ab`, check “Visible to all YSE users…”, post “test public”. As `sec_user_ac`, comment **must** appear.
6. **Comment — group B only:** as `sec_user_ab`, uncheck public, select only `sec-group-b`, post “test B only”. As `sec_user_b` — visible; as `sec_user_ac` — **not** visible.
7. **Follow-up — default groups:** as `sec_user_ab`, add follow-up on `SecVis-Cls-mag0-public` with default eligible groups checked. As `sec_user_ac`, follow-up row **must** appear.
8. **Follow-up — Public group:** on `SecVis-Cls-mag0-public`, check only **Public**, submit. As any user in the Public group with transient access — visible. On `SecVis-Cls-mag2-grpB`, **Public** must be greyed out and unchecked.
9. **Follow-up — restricted:** select `SecVis-Cls-mag2-grpB`, keep only `sec-group-b` checked, submit. As `sec_user_b` — visible; as `sec_user_ac` — **not** visible.
10. **Follow-up — no groups:** select `SecVis-Cls-mag2-grpB`, uncheck all groups, submit — form **must** reject with a validation error (red message above Submit).
11. **Follow-up — submit UX:** after a validation error, fix the selection and submit again without hard refresh; follow-up list should reload.
12. **Follow-up — `/followup/` page:** as `sec_user_ab`, `SecVis-Cls-mag4-grpD` section must **not** appear; as `sec_user_d`, `SecVis-Cls-mag2-grpB` must **not** appear.

#### Observing resources (follow-up requests)

`seed_security_test_matrix` also creates **24 observing resources** (8 classical + 8 ToO + 8 queued) on the matrix transient, using the same mag/group labeling as photometry:

| Mag | Groups | Telescope suffix example |
|-----|--------|--------------------------|
| 0 | public | `SecVis-Cls-mag0-public` |
| 1 | A | `SecVis-Too-mag1-grpA` |
| 2 | B | `SecVis-Que-mag2-grpB` |
| … | … | … |

Each test user sees the same mag numbers in resource dropdowns as on the light curve (e.g. `sec_user_b` → mags `0, 2, 5, 7`).

1. Re-seed: `docker exec ysepz_web_container python3 manage.py seed_security_test_matrix`
2. Open `/transient_detail/secvis-matrix/` → **Follow-up** tab → **Add Transient Follow-up**
3. As `sec_user_b`, Classical/ToO/Queued dropdowns should list `mag0`, `mag2`, `mag5`, `mag7` resources only — not `mag1-grpA`.
4. Submit a follow-up using `SecVis-Cls-mag2-grpB` and verify audience controls separately (steps 7–10 above).
5. **Observing calendar:** after re-seed, open `/observing_calendar/` as `sec_user_ab` — only classical `SecVis-Cls-*` nights for resources you may use (mags `0, 1, 2, 5, 6, 7`); `mag3-grpC` and `mag4-grpD` must **not** appear. As `sec_user_d`, only `mag0` and `mag4` appear.

Automated tests: `YSE_App.tests.test_security_matrix_resources`.

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
- `creator_only` observing resources (extension point exists; no production rows yet)

### v1 audience UI — stage status (2026-06)

| Area | Status |
|------|--------|
| Comment create-time audience (private default, public opt-in, creator-only) | **done** |
| Follow-up create-time audience (group checkboxes, Public for public resources) | **done** |
| Follow-up visibility filter (groups + linked resource; `/followup/` page) | **done** |
| Observing calendar group filter | **done** |
| Deferred follow-up form submit (validation + AJAX in early script) | **done** |
| Security matrix seed + `ClassicalObservingDate` for calendar | **done** |
| Automated tests (`test_audience_ui_v1`, `test_security_matrix_resources`, `test_group_visibility`) | **done** |
