# Nexus landing — Figma notes

**File:** `ztZwfo2BBvrWNlUijXeJ4N` · Page `7:10` “hero new” · Frame `7:11` “Html → Body”  
**Session:** `4328c883-56ff-4c80-9ea3-34c45c8410b1`  
**Canvas width:** 1280 (not 1440). Height ~7375.  
**Mobile frame:** none in file (no 390-wide sibling).  
**Variables:** `get_variable_defs` returned `{}` — using prompt fallback tokens + extras below.

## Top-level sections (messy HTML-export names)

| Order | Expected | Figma name | Node | Size / notes |
|------:|----------|------------|------|--------------|
| 1 | Navigation | Header | `7:757` | 1280×80, sticky glass |
| 2 | Hero | SECTION 1: HERO | `7:442` | 1280×1009.75 |
| 3 | Product image | SECTION 2: HERO PRODUCT… | `7:469` | nested in hero; shell 1200×438.5, r16 |
| 4 | Logo strip | SECTION 3: LOGO STRIP | `7:14` | y≈1010, h198 |
| 5 | Bento features | SECTION 4: FEATURES BENTO… | `7:38` | y≈1208, h1638; 12-col grid |
| 6 | Workflow | SECTION 5: WORKFLOW… | `7:216` | y≈2846, h910 |
| 7 | Numbers | SECTION 6: NUMBERS… | `7:310` | y≈3756, h328 |
| 8 | Testimonial | SECTION 7: TESTIMONIAL | `7:336` | y≈4084, h578 |
| 9 | Security strip | SECTION 8: SECURITY… | `7:350` | y≈4662, h703 |
| 10 | FAQ | SECTION 9: FAQ ACCORDION | `7:384` | y≈5365, h897 |
| 11 | Final CTA | SECTION 10: FINAL CTA | `7:424` | y≈6262, h755 |
| 12 | Footer | Footer | `7:697` | y≈7098, h278 |

Names are long/SECTION-prefixed; many anonymous “Container” / “Background” layers.

## Fonts in Figma (pairing)
- **Display:** Newsreader Variable (regular + italic) — preloaded from `/fonts/`
- **Sans:** Geist Variable (`@fontsource-variable/geist/wght.css`)
- **Mono:** Geist Mono Variable (`@fontsource-variable/geist-mono/wght.css`)
- JetBrains Mono in file → Geist Mono
- Max 3 families on the landing page

## Colour system (`.landing`)
- Dark default: forest `#050D0A` + emerald accent `#34D3A0`; italic headline word uses `--highlight` cream
- Light “Sea Foam” via `data-landing-theme="light"` (tokens defined; not applied yet)
- On light surfaces never use `--accent` as text — use `--accent-text`

## Hero measurements
- Padding: pt 64 / pb 112 / px 32
- Eyebrow pill: mono 13px, tracking 0.65px, warm text, amber 6px dot
- H1: Newsreader 72px / lh 72–76, tracking -2.16px; “forward.” italic accent
- Subhead: Geist 17px / lh 27.63, text @ 90%
- Primary CTA: accent fill, text `#070a14`, px24 py12, r10
- Secondary: surface-1 fill, inset highlight, ⌘D chip surface-2
- Micro: mono 12px muted
- Glow discs: indigo blur 140 / amber blur 130
- Board margin-top 64; perspective tilt intended via motion

## Nav
- h80, px32; logo mark 32×32 r8 surface-chip; wordmark Newsreader 24px
- Badge: “v1.0 now in beta”
- Links: Product / Workflow / Security / Docs — Geist 15px warm
- Start free: accent, text `#704800`, r8
- Avatar circle accent-soft 32

## Bento (12-col, gap 24, section py 128 px 40)
1. Board Engine span 8 row1 — “Kanban that keeps up”
2. Keyboard span 4 row1 — “Command everything”
3. Cycle span 4 row2 — “Backlog and sprints”
4. Isolation span 4 row2 — “Tenant isolation”
5. Audit span 4 row2 — “Immutable records”
6. Velocity span 8 row3 — “Reports that explain”
Tile: surface-1, r16, p32, inset highlight

## Remaining sections (from metadata — Figma MCP rate-limited mid-build)

### Logo strip `7:14`
- Label: BUILT FOR TEAMS THAT SHIP
- Logos: KINETIX AETHER MONOLITH VELOCE SYNTHETIX ORBITAL HYPERPLANE BASEFORM
- bg `#0b0e18` → `--surface-logo`; opacity 60% row

### Workflow `7:216`
- H2: How software gets shipped on Nexus.
- Steps Plan / Build / Ship (short titles from widths); bodies in metadata
- Panel: Implement tenant schema partitioning + meta + subtasks

### Numbers `7:310`
- 100ms / 5 / 3 / 0 with known captions

### Testimonial `7:336`
- Quote known; attribution ER / Elena Rostova inferred (initials node)

### Security `7:350`
- Cards: Workspace isolation, Role-based access, Audit log (bodies known)
- H2 width ~625 → Architected for data sovereignty.

### FAQ `7:384`
- FAQ1 answer known; Q1 inferred “How is Nexus different from Jira?”
- Q2–Q5 widths used to draft adjacent questions (flag for Figma re-check)

### Final CTA `7:424`
- Email placeholder name@company.com; heading “Move your team forward.”

### Footer `7:697`
- Product / Developers / Company / Legal columns (exact link labels from metadata)

## Extra tokens (from Figma hex, named)
- `--text-warm` #D6C4AF
- `--text-bright` #E0E2F1
- `--accent-ink` #704800
- `--accent-soft` #FFD9AB
- `--surface-chip` #262A35
- `--surface-elevated` #313440
- `--surface-active` #18213A
- `--nav-glass` rgb(11 14 24 / 0.8)
- `--success-mint` #64F9BC
- `--avatar-indigo` #2233B9
- `--lavender` #BCC2FF
- `--traffic-red/yellow/green` rgba traffic lights
