# Go / No-Go Checklist (Release Train F)

Decision gate before merging the implementation branch to main and tagging.
ANY "No" = NO-GO.

| # | Criterion | Yes/No |
|---|---|---|
| 1 | Full UAT checklist passed on VPS (docs/UAT_CHECKLIST.md) | |
| 2 | `run_full_validation.sh` green on the VPS runtime | |
| 3 | Safety Matrix SAFE with production `.env` defaults | |
| 4 | Secret scan clean; manual spot-check of `git log -p` for the branch shows no secrets | |
| 5 | No strategy file modified: `git diff phase-7a-approved..HEAD -- tasi_engine_v7_2_1.py backend/core/classifier.py backend/core/regime.py backend/core/sizes.py backend/core/chandelier.py backend/core/executor.py backend/core/universe.py` is EMPTY | |
| 6 | All send/scheduler/preview/smoke flags false in runtime `.env` | |
| 7 | App unreachable from public internet | |
| 8 | Backup taken immediately before merge | |
| 9 | Rollback path tested (runbook §2) at least once | |
| 10 | Reviewer (human) has read RELEASE_TRAIN reports and this branch's diff | |

## On GO
1. Merge branch to main (fast-forward or merge commit per repo convention).
2. Tag: `release-trains-a-f-approved`.
3. Deploy the tag per runbook §1; re-run UAT sections A, C, D.

## On NO-GO
1. Record failing criteria in the review thread.
2. Fix on the same branch; rerun the full checklist.
