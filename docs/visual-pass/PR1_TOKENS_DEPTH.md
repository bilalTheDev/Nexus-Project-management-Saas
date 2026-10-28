# PR1 — Tokens + depth system

Surface-only pass. No motion libraries, no command palette, no dashboard bento redesign.

## What changed

- Brand-aligned CSS tokens (Warm Paper `#FAF9F5`, Teal `#347D78`, Soft Mint `#E5F1EC`, text/border scales)
- Semantic aliases: `--bg`, `--surface`, `--surface-raised`, `--border`, `--text`, `--accent`, `--danger`, …
- Dark theme with 3 elevations (paper / surface / raised) and glow-forward emphasis
- Depth utilities: `surface-card`, `shadow-raised`, inset highlight, page noise texture, teal hero glow
- Glass sidebar (`sidebar-glass`) + active nav left accent bar
- Glass top bar; raised cards on dashboard and auth panel
- Priority/status pills and form errors use semantic tokens (theme-safe)

## Explicitly deferred to later PRs

- Magic UI / shadcn / motion / cmdk / sonner / recharts
- Cmd+K, route transitions, bento dashboard, split login layout
