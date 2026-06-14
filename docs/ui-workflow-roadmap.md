# YSE UI / workflow roadmap

**Canonical repo:** https://github.com/Young-Supernova-Experiment/YSE_PZ  
**Integration branch:** `develop` (phase PRs merge here)  
**Release:** `master` after thorough `develop` testing  
**Last updated:** 2026-06-04

**Workflow:** one branch per phase → PR to `develop` → test on `develop` → promote `develop` → `master`  
**UI sequence:** **A** (phase 1 theme) → **B** (phase 7 Bootstrap 5) → **C** (HTMX islands in phases 2 and 4)

Living plan (full catalog, testing pyramid): `.cursor/plans/yse_ui_workflow_roadmap_2455eacc.plan.md`  
Issue number log: [`docs/ui-workflow-issues-yse.log`](ui-workflow-issues-yse.log)

---

## Current status

| Phase | Branch | PR | State |
|-------|--------|-----|--------|
| **0** | `ui/phase-0-bugfixes` | [#93](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/93) → `develop` | **Ready to merge** — CI `docker-test` green; closes #16–#23 |
| **1** | `ui/phase-1-theme` | [#94](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/94) → `develop` (stacked on #93) | **Ready for review** — theme + transient_detail perf + TNS fixture (#95–#99) |
| 2–7 | see [Branches](#branches-base-ysedevelop) | — | Not started |

### Phase 0 deliverables (on branch)

- Stable table sort (`stable_order_by`, dashboard `-disc_date`, `-pk`)
- Observing-night / follow-up name sort (`transient__name`)
- Tag PATCH no-op + JS fix on transient detail
- Vendored `bokeh-2.4.2.min.js`; summary LC real DQ labels
- `PhotometricBandSerializer` `disp_symbol` fix
- Tests: `YSE_App/tests/test_phase0_ui_bugfixes.py` (org issues #16–#23)

**Deferred to later phases:** davecoulter#132 (tag search) → phase 6 #86; #177 (FITS viewer) → phase 6 #87

---

## Next steps (ordered)

### 1. Merge phase 0 (now)

1. Review [PR #93](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/93); confirm body includes `Fixes #16` … `Fixes #23`.
2. Merge into **`develop`** (squash or merge commit per team preference).
3. Locally: `git fetch yse develop && git checkout develop && git pull yse develop`.
4. Close or verify auto-closed issues **#16–#23**.

**PR test checklist (already run in CI; re-run locally if needed):**

```bash
docker exec ysepz_web_container python3 manage.py test YSE_App.tests.test_phase0_ui_bugfixes --verbosity=2
docker exec ysepz_web_container python3 manage.py test YSE_App.tests.test_page_load_regression --verbosity=2
```

### 2. Deploy / validate on server (after merge to `develop` or `master`)

1. Pull deployed branch; restart Gunicorn (or app container).
2. `python3 manage.py collectstatic --noinput` — required for new `bokeh-2.4.2.min.js`.
3. Confirm `/static/YSE_App/bokeh-2.4.2.min.js` returns 200.
4. Smoke: login, dashboard pagination/sort, observing night name sort, transient detail tags, open light curve (no Bokeh 404).
5. **Proxy/timeouts:** Apache or nginx `ProxyTimeout` / `proxy_read_timeout` ≥ Gunicorn `GUNICORN_TIMEOUT` (default **120s** in [`docker/entrypoints/docker-compose-up-entrypoint.sh`](../docker/entrypoints/docker-compose-up-entrypoint.sh)).
6. Production: `IS_DEBUG=False`, `DJANGO_SECRET_KEY` via env; optional `REDIS_URL` if multiple Gunicorn workers.

### 3. Phase 1 — theme + perf + TNS fixture (UI path **A**) — **implemented, PR #94**

**Branch:** `ui/phase-1-theme` → [PR #94](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/94) (**ready for review**, stacked on #93).

**Closes:** #24–#32 (P1-1 … T1-1) and #95–#99 (transient_detail perf, TNS fixture, photometry map, calendar UX, static fixes).

**Before merge:**

1. Merge **#93** into `develop`.
2. Rebase #94: `git fetch yse develop && git rebase yse/develop && git push --force-with-lease yse ui/phase-1-theme`.
3. Run PR #94 test plan (theme, TNS map, HAR snapshots, `test_page_load_regression`, `test_performance`).
4. Manual smoke: `2026fba` / `2026fov` on transient_detail; `collectstatic` for theme + Aladin vendor.

**Plans:** `.cursor/plans/phase_1_theme_plan_10271da7.plan.md` (checklists), `.cursor/plans/yse_ui_workflow_roadmap_2455eacc.plan.md` (full roadmap).

**Optional:** refresh SQL fixture — `build_tns_fixture --prefix 2026f --max 50 --merge-manifest --clobber` then `build-test-fixture-db.sh export`.

### 4. Phase 2 — comments + Slack (**C**) — **implemented, [PR #103](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/103)**

**Branch:** `ui/phase-2-comments-slack` → `develop` (**stacked on #94**; PR base `ui/phase-1-theme` until #93/#94 merge).

**Closes:** #49–#58 (P2-1 … P2-10), T2-1 [#33](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/33).

**Follow-up issues (not in this PR):** [#102](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/102) (group access security), [#100](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/100) (per-group Slack), [#101](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/101) (Slack ops doc).

**Before merge:**

1. Merge **#93** and **#94** into `develop` (or rebase this branch onto `yse/develop` after they land).
2. `git fetch yse develop && git rebase yse/develop && git push --force-with-lease yse ui/phase-2-comments-slack`.
3. Run `YSE_App.tests.test_phase2_comments`; smoke: Summary tab comment thread, optional Slack env in `docker/.env.secrets`.
4. `python manage.py migrate` for `0004_slackthreadlink`.

**Plans:** `.cursor/plans/phase_2_comments_slack_plan_10271da7.plan.md`, groups security plan (separate track).

### 5. Phases 3–7 (after prior phase merges)

| Phase | Branch | Issues | Theme |
|-------|--------|--------|--------|
| **2** | *(see §4)* | #49–#58, #33 | *(shipped on `ui/phase-2-comments-slack`)* |
| **2b** | `ui/security-group-access` → [PR #104](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/104) | [#102](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/102) — visibility module, private comments, Explorer staff-only |
| **3** | `ui/phase-3-night-requests` | #59–#69, T3-1 #34 | `ClassicalNightRequest`, priority, night-scoped queryset fixes |
| **4** | `ui/phase-4-classical-scheduler` | #70–#78, T4-1 #35 | Greedy scheduler + planner UI + export (**C**) |
| **5** | `ui/phase-5-dq-bitmask` | #79–#85, T5-1 #36 | `quality_mask` dual-write, filters, plot muting |
| **6** | `ui/phase-6-plots-fits` | #86–#92, T6-1 #37 | Markers, FITS viewer (#177), tag Select2 (#132) |
| **7** | `ui/phase-7-bootstrap5` | #38–#45, T7-1 #45 | Bootstrap 5 + retire AdminLTE shell (**B**) |

Phases **5** and **6** may start after **4** if team capacity allows; **7** should follow **1** (theme tokens inform BS5 migration).

### 6. Release to production

1. Soak test on **`develop`** (Docker or staging).
2. PR **`develop` → `master`** when stable.
3. Deploy `master`; repeat collectstatic + smoke from step 2.

### 7. Docs / meta (parallel, low priority)

- [#46](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/46) — optional GitHub Project board  
- [#47](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/47) — align `CONTRIBUTING.md` with `develop` + org issue tracker  
- [#48](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/48) — document test pyramid (see [Testing](#testing))

**Interim tracker:** [astrofoley/YSE_PZ #34–#110](https://github.com/astrofoley/YSE_PZ/issues) — superseded by org **#16–#92**; link in PR bodies when referencing old numbers.

---

## Testing

| Layer | Location | When |
|-------|----------|------|
| Unit | `YSE_App/tests/test_phase0_ui_bugfixes.py`, per-phase `T*-1` | Every phase PR |
| Performance | `test_page_load_regression.py`, `test_performance.py`, `docs/perf/har_snapshots/*.json` | UI/view/template changes |
| Smoke | `test_smoke.py` | End of each phase |
| Global policy | [#48](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/48) | Meta |

**Env vars (perf):** `YSE_PERF_SKIP_TIMING=1`, `YSE_PERF_RECORD_PATH=…` — see [CONTRIBUTING.md](../CONTRIBUTING.md).

Each phase PR should include:

```markdown
## Tests run
- [ ] manage.py test YSE_App.tests.test_<phase> ...
- [ ] test_page_load_regression (if views/templates touched)
## Diagnostics
- TTFB / query count: unchanged | new baseline (justify)
```

---

## Phase 0 PR closes

Fixes #16 Fixes #17 Fixes #18 Fixes #19 Fixes #20 Fixes #21 Fixes #22 Fixes #23

---

## Branches (base: `yse/develop`)

| Phase | Branch |
|-------|--------|
| 0 | `ui/phase-0-bugfixes` |
| 1 | `ui/phase-1-theme` |
| 2 | `ui/phase-2-comments-slack` |
| 2b | `ui/security-group-access` |
| 3 | `ui/phase-3-night-requests` |
| 4 | `ui/phase-4-classical-scheduler` |
| 5 | `ui/phase-5-dq-bitmask` |
| 6 | `ui/phase-6-plots-fits` |
| 7 | `ui/phase-7-bootstrap5` |

---

## Issue index

| Catalog ID | Issue |
|------------|-------|
| P0-1 | [#16](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/16) |
| P0-2 | [#17](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/17) |
| P0-3 | [#18](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/18) |
| P0-4 | [#19](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/19) |
| P0-5 | [#20](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/20) |
| P0-6 | [#21](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/21) |
| P0-7 | [#22](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/22) |
| T0-1 | [#23](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/23) |
| P1-1 | [#24](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/24) |
| P1-2 | [#25](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/25) |
| P1-3 | [#26](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/26) |
| P1-4 | [#27](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/27) |
| P1-5 | [#28](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/28) |
| P1-6 | [#29](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/29) |
| P1-7 | [#30](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/30) |
| P1-8 | [#31](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/31) |
| T1-1 | [#32](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/32) |
| P2-1 | [#49](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/49) |
| P2-2 | [#50](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/50) |
| P2-3 | [#51](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/51) |
| P2-4 | [#52](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/52) |
| P2-5 | [#53](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/53) |
| P2-6 | [#54](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/54) |
| P2-7 | [#55](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/55) |
| P2-8 | [#56](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/56) |
| P2-9 | [#57](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/57) |
| P2-10 | [#58](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/58) |
| T2-1 | [#33](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/33) |
| P3-1 | [#59](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/59) |
| P3-2 | [#60](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/60) |
| P3-3 | [#61](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/61) |
| P3-4 | [#62](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/62) |
| P3-5 | [#63](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/63) |
| P3-6 | [#64](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/64) |
| P3-7 | [#65](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/65) |
| P3-8 | [#66](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/66) |
| P3-9 | [#67](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/67) |
| P3-10 | [#68](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/68) |
| P3-11 | [#69](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/69) |
| T3-1 | [#34](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/34) |
| P4-1 | [#70](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/70) |
| P4-2 | [#71](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/71) |
| P4-3 | [#72](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/72) |
| P4-4 | [#73](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/73) |
| P4-5 | [#74](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/74) |
| P4-6 | [#75](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/75) |
| P4-7 | [#76](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/76) |
| P4-8 | [#77](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/77) |
| P4-9 | [#78](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/78) |
| T4-1 | [#35](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/35) |
| P5-1 | [#79](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/79) |
| P5-2 | [#80](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/80) |
| P5-3 | [#81](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/81) |
| P5-4 | [#82](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/82) |
| P5-5 | [#83](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/83) |
| P5-6 | [#84](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/84) |
| P5-7 | [#85](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/85) |
| T5-1 | [#36](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/36) |
| P6-1 | [#86](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/86) |
| P6-2 | [#87](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/87) |
| P6-3 | [#88](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/88) |
| P6-4 | [#89](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/89) |
| P6-5 | [#90](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/90) |
| P6-6 | [#91](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/91) |
| P6-7 | [#92](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/92) |
| T6-1 | [#37](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/37) |
| P7-1 | [#38](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/38) |
| P7-2 | [#39](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/39) |
| P7-3 | [#40](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/40) |
| P7-4 | [#41](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/41) |
| P7-5 | [#42](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/42) |
| P7-6 | [#43](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/43) |
| P7-7 | [#44](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/44) |
| T7-1 | [#45](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/45) |
| META-1 | [#46](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/46) |
| META-2 | [#47](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/47) |
| TEST-GLOBAL | [#48](https://github.com/Young-Supernova-Experiment/YSE_PZ/issues/48) |
