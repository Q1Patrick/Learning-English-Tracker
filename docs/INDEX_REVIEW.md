# Person 3 — Index review (10/11/2026)

Scope: SQLite query plans on a disposable database. No index or migration was applied to the learner database.

## Queries and selected indexes

| Query | New index | Reason |
|---|---|---|
| One user's newest quiz attempts, ordered by `-completed_at, -id` | `quiz_user_completed_idx (user, -completed_at, -id)` | Supports both the owner predicate and deterministic history ordering |
| One user's quiz attempts within a timestamp range | Same index | Supports the owner predicate followed by a time range |
| Admin's global attempt timeline/date range | `quiz_completed_idx (-completed_at, -id)` | The user-leading index does not support a timeline across all users |
| One user's study sessions in day/week ranges | `study_user_studied_idx (user, -studied_at)` | Supports existing dashboard filters and session ordering |

Foreign keys already index user/quiz IDs. Vocabulary already has `(user, mastery_level)` and unique `(user, word)`; DailyGoal has unique `(user, target_date)`. Their existing indexes remain unchanged. These B-tree indexes do not imply substring searches become fast.

## Experiment

Dataset: 12 synthetic users, 4,800 quiz attempts and 4,800 study sessions. Time values span 400 hours per user, with the same timestamp reused across users. The query uses `LIMIT 20` for history; interval variants use a seven-day timestamp range.

Before the candidate indexes, SQLite used the existing user FK indexes for private queries and a temporary B-tree for ordering. The admin query scanned the attempt table and also used a temporary ordering B-tree.

After adding the candidates in the disposable database:

```text
private_history: SEARCH quizzes_quizattempt USING INDEX quiz_user_completed_idx (user_id=?)
private_recent: SEARCH quizzes_quizattempt USING INDEX quiz_user_completed_idx (user_id=? AND completed_at>?)
global_admin_recent: SEARCH quizzes_quizattempt USING INDEX quiz_completed_idx (completed_at>?)
user_study_range: SEARCH learning_studysession USING INDEX study_user_studied_idx (user_id=? AND studied_at>?)
```

No temporary ordering B-tree appeared in these after-plans. This supports the index choice; it is not a production latency benchmark or a speed-up percentage. Indexes consume storage and add write work, and live index creation may lock SQLite writers. Recheck against the actual database size/workload before live migration.

## Migration and rollback

New migrations are `quizzes/0006_history_query_indexes.py` and `learning/0002_history_query_indexes.py`. They add indexes only and keep prior migrations unchanged. Their reverse operations remove only the new indexes; this does not justify reversing earlier history/constraint migrations, which can remove stored fields.

The verification script tests fresh migrations and upgrades on a read-only backup of an existing database, checks foreign keys/integrity and compares learner row counts. Live migration remains a separate, approved step with a recoverable backup and validation on the real application database, as required in Person3.md.
