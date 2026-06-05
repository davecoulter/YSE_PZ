# Group-based access control

YSE uses Django **collaboration groups** (`auth.Group`) on photometry, spectra, and telescope resources. Survey `ObservationGroup` on transients is metadata only.

## Rules

- **Empty `groups` M2M** on photometry/spectra/resources: visible to all logged-in users (unchanged).
- **New transient comments**: private by default (`Log.is_public=False` with `Log.groups` set to shared collaboration groups). Opt-in `is_public=True` for all collaborators who can open the transient.
- **Legacy comments** (before migration `0005_log_visibility`): `is_public=True`, no groups — unchanged visibility.

## Code

- [`YSE_App/services/visibility.py`](../YSE_App/services/visibility.py) — shared helpers
- [`YSE_App/services/comments.py`](../YSE_App/services/comments.py) — comment create/list filtering

## SQL Explorer

Staff-only (`EXPLORER_PERMISSION_VIEW` / `CHANGE` in settings). Dashboard and canvas SQL results are post-filtered with `filter_transients_by_user_access`.

## Follow-ups

Per-group Slack ([#100](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/100)), follow-up `is_public` filtering, and DRF hardening remain on [#102](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/102).
