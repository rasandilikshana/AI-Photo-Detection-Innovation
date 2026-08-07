#!/usr/bin/env python
"""Re-analyse stored submissions against the current pipeline.

Stored verdicts are not recomputed when the pipeline changes, so records written by an
earlier version stay on the judge panel indefinitely. Submission 45 in particular read
APPROVED / AUTHENTIC long after the provenance checks that reject it were deployed,
which is actively misleading in front of a judge.

Usage, from src/backend/ai-detection-service on the server:

    BACKFILL_DSN=postgresql://user:pass@localhost/avar_db \\
      ./venv/bin/python scripts/backfill_verdicts.py --dry-run --stale
    BACKFILL_DSN=... ./venv/bin/python scripts/backfill_verdicts.py --stale

--stale selects every submission whose stored details predate the Authenticity Score
(no 'authenticity' key). --ids re-runs specific submissions regardless.

ALWAYS run --dry-run first and read the diff: this mutates judge-visible records. Take a
backup first (see the hardening plan, Task 8 Step 2).
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg
import httpx

DETECTION_URL = os.getenv("DETECTION_URL", "http://127.0.0.1:8001/api/v1/analyze")

# Mirrors verdict_map in competition-service/app/routes/submissions.py. Kept in sync
# deliberately: a mismatch here would write statuses the API would never produce.
VERDICT_MAP = {
    "AUTHENTIC": ("APPROVED", "AUTHENTIC"),
    "REJECT": ("REJECTED", "AI_GENERATED"),
    "QUARANTINE": ("PENDING", "SUSPICIOUS"),
}

SELECT_COLUMNS = (
    "id, title, jpg_file_url, raw_file_url, status::text as status, "
    "verification_verdict::text as verdict, verification_confidence as confidence"
)


async def fetch_targets(conn, ids, stale):
    if ids:
        return await conn.fetch(
            f"select {SELECT_COLUMNS} from submissions where id = any($1::int[]) order by id", ids
        )
    if stale:
        return await conn.fetch(
            f"select {SELECT_COLUMNS} from submissions "
            "where verification_details is not null "
            "and not (verification_details::jsonb ? 'authenticity') order by id"
        )
    return []


async def reanalyse(jpg: str, raw: str) -> dict:
    with open(jpg, "rb") as jpg_handle, open(raw, "rb") as raw_handle:
        files = {
            "jpg_file": (Path(jpg).name, jpg_handle.read(), "image/jpeg"),
            "raw_file": (Path(raw).name, raw_handle.read(), "application/octet-stream"),
        }
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(DETECTION_URL, files=files)
    response.raise_for_status()
    return response.json()


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", type=int, nargs="+", help="specific submission ids")
    parser.add_argument("--stale", action="store_true",
                        help="every submission whose details predate the Authenticity Score")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dsn", default=os.getenv("BACKFILL_DSN"))
    args = parser.parse_args()

    if not args.dsn:
        sys.exit("set BACKFILL_DSN, e.g. postgresql://user:pass@localhost/avar_db")
    if not args.ids and not args.stale:
        sys.exit("pass --ids or --stale")

    conn = await asyncpg.connect(args.dsn)
    try:
        rows = await fetch_targets(conn, args.ids, args.stale)
        if not rows:
            print("nothing to do")
            return 0

        print(f"{len(rows)} submission(s) selected\n")
        updated = skipped = failed = 0

        for row in rows:
            jpg, raw = row["jpg_file_url"], row["raw_file_url"]
            label = f"  {row['id']:>3} {(row['title'] or '')[:26]:26}"

            if not jpg or not Path(jpg).exists():
                print(f"{label} SKIP  jpg missing on disk")
                skipped += 1
                continue
            if not raw or not Path(raw).exists():
                print(f"{label} SKIP  raw missing on disk")
                skipped += 1
                continue

            try:
                result = await reanalyse(jpg, raw)
            except Exception as e:
                print(f"{label} FAIL  {type(e).__name__}: {str(e)[:60]}")
                failed += 1
                continue

            status, verdict = VERDICT_MAP.get(result["verdict"], ("PENDING", "NEEDS_REVIEW"))
            score = (result.get("authenticity") or {}).get("score")
            arrow = "==" if (status, verdict) == (row["status"], row["verdict"]) else "=>"
            print(f"{label} {row['status']}/{row['verdict']} {arrow} {status}/{verdict}  score={score}/100")

            if not args.dry_run:
                await conn.execute(
                    "update submissions set status = $1::submissionstatus, "
                    "verification_verdict = $2::verificationverdict, "
                    "verification_confidence = $3, verification_details = $4, "
                    "verification_timestamp = $5 where id = $6",
                    status, verdict, result.get("confidence_score", 0.0),
                    json.dumps(result), result.get("timestamp", ""), row["id"],
                )
                updated += 1

        print(f"\n{'DRY RUN - nothing written' if args.dry_run else f'{updated} updated'}"
              f"{f', {skipped} skipped' if skipped else ''}"
              f"{f', {failed} failed' if failed else ''}")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
