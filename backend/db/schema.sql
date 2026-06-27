-- SETU SQLite schema. JSON-typed columns hold serialized lists/vectors (TEXT).
-- Migrate to Postgres+pgvector only if scale demands it; at demo scale brute-force cosine in
-- Python over this table is instant and reliable.

CREATE TABLE IF NOT EXISTS persons (
    id                      TEXT PRIMARY KEY,
    role                    TEXT NOT NULL CHECK (role IN ('lost', 'found')),

    age_band                TEXT NOT NULL DEFAULT 'unknown',
    gender                  TEXT NOT NULL DEFAULT 'unknown',
    name                    TEXT,                       -- nullable: ~15% have no name
    clothing                TEXT NOT NULL DEFAULT '[]', -- json list
    distinguishing_features TEXT NOT NULL DEFAULT '[]', -- json list
    height_band             TEXT NOT NULL DEFAULT 'unknown',
    languages_spoken        TEXT NOT NULL DEFAULT '[]', -- json list
    last_seen_location      TEXT,
    last_seen_time          TEXT,                       -- ISO 8601

    reporter_name           TEXT,
    reporter_mobile         TEXT,                       -- nullable: ~20% have no mobile

    spoken_language         TEXT NOT NULL DEFAULT 'unknown',
    raw_transcript          TEXT NOT NULL DEFAULT '',
    native_summary          TEXT NOT NULL DEFAULT '',

    face_embedding          TEXT,                       -- json list[float] (512-d) or NULL
    photo_storage_key       TEXT,
    photo_location_hint     TEXT,

    is_minor                INTEGER NOT NULL DEFAULT 0,
    consent_given           INTEGER NOT NULL DEFAULT 0,

    centre_id               TEXT NOT NULL,
    centre_zone             TEXT,
    status                  TEXT NOT NULL DEFAULT 'open'
                              CHECK (status IN ('open', 'matched', 'reunited', 'expired')),

    created_at              TEXT NOT NULL,
    ttl_expires_at          TEXT NOT NULL,
    updated_at              TEXT NOT NULL,

    -- evaluation harness: links a synthetic lost/found pair; NULL for real records
    test_pair_id            TEXT,
    test_should_match       INTEGER                     -- 1 positive pair, 0 negative pair, NULL n/a
);

CREATE INDEX IF NOT EXISTS idx_persons_role_status ON persons(role, status);
CREATE INDEX IF NOT EXISTS idx_persons_centre      ON persons(centre_id);
CREATE INDEX IF NOT EXISTS idx_persons_age_gender  ON persons(age_band, gender);
CREATE INDEX IF NOT EXISTS idx_persons_minor       ON persons(is_minor);
CREATE INDEX IF NOT EXISTS idx_persons_ttl         ON persons(ttl_expires_at);
CREATE INDEX IF NOT EXISTS idx_persons_testpair    ON persons(test_pair_id);

-- Full-text fallback search over name + transcript (FTS5). Maintained by the repo on write.
CREATE VIRTUAL TABLE IF NOT EXISTS persons_fts USING fts5(
    person_id UNINDEXED, name, raw_transcript, tokenize = 'unicode61'
);

CREATE TABLE IF NOT EXISTS audit_log (
    id                 TEXT PRIMARY KEY,
    actor              TEXT NOT NULL,
    action             TEXT NOT NULL,
    person_id          TEXT,
    related_person_id  TEXT,
    meta               TEXT NOT NULL DEFAULT '{}',
    timestamp          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_person ON audit_log(person_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_time   ON audit_log(timestamp);

-- Proactive match notifications surfaced on the ops dashboard.
CREATE TABLE IF NOT EXISTS notifications (
    id               TEXT PRIMARY KEY,
    type             TEXT NOT NULL,
    lost_person_id   TEXT,
    found_person_id  TEXT,
    score            REAL,
    explanation      TEXT NOT NULL DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'new',   -- new | seen | actioned
    created_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notif_status ON notifications(status);

CREATE TABLE IF NOT EXISTS announcements (
    id                 TEXT PRIMARY KEY,
    person_id          TEXT NOT NULL,
    target_language    TEXT NOT NULL,
    announcement_text  TEXT NOT NULL DEFAULT '',
    audio_storage_key  TEXT,
    triggered_by       TEXT NOT NULL,
    was_broadcast      INTEGER NOT NULL DEFAULT 0,
    is_minor_blocked   INTEGER NOT NULL DEFAULT 0,
    created_at         TEXT NOT NULL
);
