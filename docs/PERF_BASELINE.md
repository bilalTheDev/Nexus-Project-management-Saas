# Nexus performance baseline (Phase 0)

**Branch:** `chore/cleanup-baseline`  
**Captured:** 2026-10-28  
**Rule:** measure first; no behavioural/API contract changes in later phases without re-measure.

---

## Stack reality check (vs Master Prompt 4 wording)

| Prompt assumes | This repo actually has |
|---|---|
| React + Vite + **TypeScript** | React + Vite + **JSX** (no `tsconfig`, no `tsc`) |
| `npx eslint .` | **`oxlint`** via `npm run lint` (no eslint config) |
| `npx vitest run` | **Not installed** (Playwright e2e only) |
| `pytest -q` | CI uses **`python manage.py test`** (Django runner); `pytest` not in requirements |

Phase 0 recorded the **repo-native** equivalents. Do not change the stack (hard constraint).

---

## Tooling / safety-net results

| Command | Result |
|---|---|
| `git switch -c chore/cleanup-baseline` | Created from `feature/security-part-a-auth` (carries uncommitted invite + perf UI work) |
| `python manage.py test` (SQLite forced: empty `DATABASE_URL` + `DATABASE_URL_UNPOOLED`) | **284 OK** in ~4.5s |
| `pytest -q` | **N/A** — module not installed; Django test runner is the project standard |
| `ruff check .` | **31 issues** (mostly import sort / unused imports); full log `docs/_baseline_ruff.txt` |
| `npx tsc --noEmit` | **N/A** — no TypeScript project; accidental `tsc` npm stub warned “not the tsc you are looking for” |
| `npx eslint .` | **N/A** — no `eslint.config.*`; use `npm run lint` → oxlint |
| `npm run lint` (oxlint) | **10 warnings**, 0 errors |
| `npx vitest run` | **N/A** — not a project dependency (install hung; aborted) |
| `npm run build` | **OK** (~1.2s); main chunk warning >500 kB |

### Characterisation tests added

`backend/apps/workspaces/tests_perf_char.py` — query-budget ceilings + task move:

- dashboard ≤ 40 queries  
- project list ≤ 20  
- board ≤ 25  
- my-tasks ≤ 25  
- activity ≤ 20  
- task position move still 200  

Also covered already: `TenantIsolationTests`, `tests_policy`, IDOR matrix.

### Seed for load

```bash
python manage.py seed_perf_load
# workspace=perf-baseline  projects=20  tasks=2000
# login=perf.baseline@example.com / PerfPass1!
```

Re-measure:

```bash
python manage.py measure_perf_baseline --out docs/perf_query_capture.json
```

---

## Backend SQL baseline (Neon, 20 projects / 2000 tasks)

Source: `docs/perf_query_capture.json` (wall/sql ms include **client↔Neon RTT**; cold starts inflate first hits).

| Endpoint | HTTP | Queries | Wall ms | SQL ms (sum) |
|---|---:|---:|---:|---:|
| dashboard | 200 | **9** | **8587** | 8391 |
| project_list | 200 | 5 | 2576 | 2500 |
| board (P01) | 200 | 5 | 1558 | 1486 |
| task_list (P01) | 200 | 6 | 1584 | 1578 |
| my_tasks | 200 | **24** | **6024** | 6000 |
| activity | 200 | 4 | 1085 | 1031 |

**Observations**

1. **Dashboard** loads essentially all workspace tasks into Python to build `projects_health` + separate COUNT queries — dominates wall time (~6.2 s attributed to one wide `tasks_task` SELECT).
2. **my_tasks** is query-heavy (24) relative to row count — likely pagination + serializer / scoping overhead.
3. **Board** is already lean on query count (5) after recent `skip_epic_progress` change; still ~1.5 s wall on Neon.
4. Local `EXPLAIN` execution times are **sub-millisecond**; most “slowness” in the capture is **network / Neon latency**, not planner cost. Still, seq scans on `tasks_task` for workspace-wide filters are Phase 3 index candidates.

### `EXPLAIN (ANALYZE, BUFFERS)` — three hottest shapes

Full text: `docs/perf_explain_top3.txt`

**1. dashboard / workspace task join** — `Seq Scan on tasks_task` (2025 rows), hash join to 20 projects.  
Execution Time: **0.689 ms** (server). Seq scan = index opportunity when table grows.

**2. project_list task scan** — same seq scan pattern. Execution Time: **0.663 ms**.

**3. board project tasks** — `Bitmap Index Scan` on `tasks_task_project_*` + sort by `position, created_at`. Execution Time: **0.096 ms**. Healthy for single-project board.

---

## Frontend bundle baseline

`npm run build` (Vite 8) — **transfer sizes for shipped chunks:**

| Asset | Raw | Gzip (vite) |
|---|---:|---:|
| **Total JS (approx)** | ~1.30 MB | **~398 kB** |
| **Initial / main chunk** `index-*.js` | **1237.7 kB** | **372.9 kB** |
| CSS `index-*.css` | 72.8 kB | 13.5 kB |
| Landing lazy chunks (sum) | ~65 kB | ~22 kB |

**vite-bundle-visualizer sunburst** (`docs/perf_bundle_stats.html`, screenshot confirmed):

| Metric | Value |
|---|---:|
| Rendered (module graph) | **2.68 MB** |
| Gzip | **786.95 KB** |
| Brotli | **679.89 KB** |

Visualizer “rendered” is the **pre-chunk graph** (larger than on-wire Vite assets). Still useful for composition: one dominant arc = nearly everything in a single main path; thin outer spikes = many small modules (icons / leaf deps). Landing sections are already lazy; **board (`@dnd-kit`), charts (`recharts`), motion, markdown** ride the main chunk today → Phase 4 route-split target.

**Note:** large JS affects **first load / TBT**, not Neon save latency. Save slowness in Phase 0 is dominated by dashboard/my-tasks SQL + RTT (see table above).

---

## Lighthouse (mobile)

**Not captured in Phase 0.** `npx lighthouse` install did not finish cleanly in this environment; no reliable headless Chrome path from the agent shell.

**Needs human review / local run:**

```bash
cd frontend && npm run preview -- --host 127.0.0.1 --port 4173
npx lighthouse http://127.0.0.1:4173/app/<slug>/dashboard --form-factor=mobile --only-categories=performance --output=json --output-path=../docs/lighthouse_dashboard.json
npx lighthouse http://127.0.0.1:4173/app/<slug>/projects/<key>/board --form-factor=mobile --only-categories=performance --output=json --output-path=../docs/lighthouse_board.json
```

Paste scores into this file before Phase 4 PRs claim Lighthouse wins.

---

## DB connection note (for later phases)

- Neon pooler URL → settings set `CONN_MAX_AGE=0` (correct for transaction pooler).
- Cold-start / first-request latency is **separate** from steady-state SQL cost (see EXPLAIN vs wall ms above).
- Do **not** add Redis in Phase 3 unless a shared cache already exists (prompt).

---

## Artefacts

| Path | Purpose |
|---|---|
| `docs/PERF_BASELINE.md` | This document |
| `docs/perf_query_capture.json` | Endpoint query counts + timings |
| `docs/perf_explain_top3.txt` | EXPLAIN ANALYZE for 3 shapes |
| `docs/perf_bundle_stats.html` | vite-bundle-visualizer |
| `docs/_baseline_ruff.txt` | ruff raw output |
| `docs/_baseline_tests.txt` | earlier test log snippet |
| `apps/workspaces/tests_perf_char.py` | characterisation tests |
| `seed_perf_load` / `measure_perf_baseline` | management commands |

---

## STOP — awaiting approval

Phase 0 complete. **No Phase 1 deletes or Phase 3/4 optimisations started.**

Suggested next step after your review: **Phase 1 dead-code audit table only** (ruff F401/vulture/knip candidates with delete/keep/human-review), one PR per area after you approve the table.
