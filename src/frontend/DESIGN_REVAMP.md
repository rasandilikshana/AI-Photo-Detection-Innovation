# A.V.A.R. Frontend Revamp — Design Language

Modern classy vibrant editorial SaaS (references: denis.io / ARTIFEXPOLA / KLYRO).
Light paper canvas, ink-black display type, pill geometry, one vivid "verified" green accent.

## Non-negotiable rules

1. **Never change script logic.** No edits to data flow, handlers, v-model bindings, ids, refs,
   API calls, or route pushes. Template class/copy changes and additive markup only.
2. All colors come from tokens. **Never** use raw palette classes (`text-green-600`,
   `bg-blue-500/10`, `bg-green-50`, `border-gray-300`, `bg-white/5`, `text-*-400`) — replace
   them with the token equivalents below when touching a line.
3. Icons stay lucide-vue-next, sized `w-4 h-4` / `w-5 h-5`. No emojis.
4. Keep every `aria-*`, `for`/`id`, `role` attribute; add `aria-label` to icon-only buttons you touch.

## Tokens (defined in src/style.css + tailwind.config.js)

| Purpose | Classes |
|---|---|
| Canvas / text | `bg-background text-foreground`, muted text `text-muted-foreground` |
| Cards | `bg-card border rounded-2xl` (radius scale: lg=1rem xl=1.25rem 2xl=1.5rem) |
| Primary action | Button default variant → ink-black pill |
| Vibrant accent | `bg-brand text-brand-foreground` (vivid green, black text) — use ONLY for: verified/authentic states, "scored" confirmation, the one hero CTA on dark sections, live/pulse dots |
| Status | `text-success` / `bg-success/10`, `text-warning` / `bg-warning/10`, `text-info` / `bg-info/10`, destructive as-is |
| Dark sections | `bg-ink text-ink-foreground`, muted text `text-ink-muted` |
| Display type | `font-display` (Space Grotesk) — h1–h3 get it automatically via base layer |

## Component recipes

- **Eyebrow badge** (above section headings):
  `<span class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">` — optionally a `<span class="h-1.5 w-1.5 rounded-full bg-brand"/>` dot.
- **Section heading**: `text-3xl md:text-5xl font-display font-semibold tracking-tight text-balance`
- **Hero headline**: `text-4xl md:text-6xl lg:text-7xl font-display font-semibold tracking-tight text-balance`
- **Buttons**: component is already pill (`rounded-full`). Variants: `default` (ink), `brand` (green — sparing), `outline`, `ghost`, `secondary`, `destructive`. Sizes unchanged.
- **Badges**: pill; variants `default|secondary|destructive|outline|success|warning|info|brand`.
- **Stat tile** (KLYRO style): `rounded-2xl border bg-card p-5` with `text-3xl font-display font-semibold` number + `text-sm text-muted-foreground` label.
- **Arrow link** (denis.io style): `inline-flex items-center gap-1 text-sm font-medium hover:gap-2 transition-all` + `<ArrowUpRight class="w-4 h-4" />`.
- **Icon tile**: `w-10 h-10 rounded-xl bg-secondary flex items-center justify-center` with `text-foreground` icon (no per-icon rainbow colors; use `text-success/text-warning/text-info/text-destructive` only when the icon itself is a status).
- **Page header**: eyebrow badge + `text-3xl md:text-4xl font-display font-semibold tracking-tight` + one-line muted description. Drop the old `w-12 h-12 rounded-xl bg-primary/10` icon-square headers.
- **Dark CTA band**: `rounded-3xl bg-ink text-ink-foreground p-8 md:p-14 overflow-hidden relative`, brand-green pill CTA inside.
- **Empty state**: icon in `w-16 h-16 rounded-full bg-secondary` circle, heading, one-line muted direction, optional CTA.
- **Loading**: always `<Loader2 class="w-8 h-8 animate-spin text-muted-foreground" />` + muted line. Never a hand-rolled border ring.
- **Hover on cards**: `transition-shadow hover:shadow-lg` (never scale transforms that shift layout). Interactive cards keep `cursor-pointer`.

## Status → token mapping (replaces old raw colors)

- approved / authentic / scored / PASS → `success` (or `brand` for the *scored-by-you* highlight)
- pending / suspicious / REVIEW / warnings → `warning`
- analyzing / info notes → `info`
- rejected / ai_generated / FAIL / errors → `destructive`

## Copy rules

- Sentence case for labels and buttons; verbs on buttons ("Save changes", not "Submit").
- Status text always Title Case chips via Badge, generated from the enum but humanized
  (`needs_review` → "Needs Review") — keep existing helper functions, don't add logic.
- No internal jargon in user-facing copy (no "V2.0", no "shared credentials testing").
