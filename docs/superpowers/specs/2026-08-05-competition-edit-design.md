# Competition Edit Feature — Design

**Date:** 2026-08-05
**Goal:** Let a competition organizer (or admin) edit a competition they created — submission deadline, max submissions per user, and other details — without breaking the existing implementation.

## Current State

- Backend (`competition-service`) already exposes `PATCH /api/v1/competitions/{id}` (`app/routes/competitions.py:update_competition`) with correct permission checks (organizer who owns it, or admin).
- Frontend already has `competitionsApi.update()` and `useCompetitionsStore.updateCompetition()` wired to that endpoint.
- **Gap 1:** `CompetitionUpdate` schema (`app/schemas.py`) only allows `title`, `description`, `rules`, `status`, `judging_start`, `judging_end`, `results_date`. It does NOT allow `submission_start`, `submission_end`, `max_submissions_per_user`, `require_raw_files`, `allow_ai_generated`, `entry_fee`, `prize_description`, `prize_amount`.
- **Gap 2:** No edit UI. `OrganizerPanel.vue` only has a create form and a read-only "My Competitions" list.

## Design

### Backend

1. **`app/schemas.py` — extend `CompetitionUpdate`** with optional fields mirroring `CompetitionCreate` constraints:
   - `submission_start`, `submission_end` (datetime)
   - `max_submissions_per_user` (int, 1–20)
   - `require_raw_files`, `allow_ai_generated` (bool)
   - `entry_fee` (int ≥ 0), `prize_description`, `prize_amount` (int ≥ 0)
   - Add the same length constraints as create to `title` (5–255) and `description` (≥ 20).
   All fields stay `Optional`/unset-aware, so existing partial updates keep working unchanged.

2. **`app/routes/competitions.py` — `update_competition`**: validate the *effective* submission window (new value if provided, else stored value): `submission_end` must be after `submission_start`, else HTTP 422. Comparison normalizes tz-aware vs naive datetimes to naive UTC, because the frontend sends ISO strings with `Z` while stored values are naive UTC.

No DB migration needed — all columns already exist on the `competitions` table. No endpoint signature changes — fully backward compatible.

### Frontend

3. **`src/types/index.ts`** — extend the `CompetitionUpdate` interface with the same optional fields.

4. **`src/views/OrganizerPanel.vue`**:
   - Use the shared `Competition` type from `@/types` (drops the narrower local interface).
   - Filter the "My Competitions" tab to the current organizer's competitions (admins see all) — implements the intent already stated in the code comment.
   - Add an **Edit** button on each owned competition card that opens a `Dialog` (existing ui/dialog components, same pattern as `JudgeDashboard.vue`) pre-filled with the competition's current values: title, description, rules, submission start/end (datetime-local), max submissions per user, prize amount/description, RAW/AI checkboxes, plus a status select (draft/open/closed/judging/completed/cancelled).
   - Save issues `PATCH /competitions/{id}` via `apiClient` (matches the file's existing direct-client pattern), converting dates to ISO and prize dollars → cents (mirror of create). Client-side end-after-start validation, inline error/success alerts, list reload on success.

### Testing

5. **`tests/test_competitions.py`** — new tests:
   - Update deadline + max submissions + prize → 200, values persisted.
   - `submission_end` before `submission_start` → 422.
   - `max_submissions_per_user` out of range → 422.
   - Non-owner participant PATCH → 403.

## Alternatives considered

- **Separate edit page/route** (`/organizer/competitions/:id/edit`): more code, new route, no added value over a dialog for a single-form edit. Rejected.
- **Restricting which fields are editable per status** (e.g. lock deadline once OPEN): adds policy complexity the product hasn't asked for; organizers legitimately extend deadlines after opening. Rejected for now (YAGNI).
