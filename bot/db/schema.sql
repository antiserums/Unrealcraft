-- Unrealcraft — Quartermaster SQLite schema
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS users (
    discord_id        INTEGER PRIMARY KEY,
    major             TEXT    NOT NULL DEFAULT 'undecided',
    minor             TEXT,
    xp                INTEGER NOT NULL DEFAULT 0,          -- quest/review/showcase XP only; chat never lands here
    rank              INTEGER NOT NULL DEFAULT -1,         -- -1 = in Orientation
    seal              TEXT,                                -- lookdev|design|anim|code (R3+)
    current_quest_id  TEXT,
    spine_done        INTEGER NOT NULL DEFAULT 0,          -- 0/1 cached
    tasters_json      TEXT    NOT NULL DEFAULT '[]',       -- injected taster ids (respec)
    streak_days       INTEGER NOT NULL DEFAULT 0,
    last_active_day   TEXT,                                -- YYYY-MM-DD, for streaks
    ue_version        TEXT,
    respec_used       INTEGER NOT NULL DEFAULT 0,
    respec_target     TEXT,                                -- major being respecced into (R3+)
    on_leave          INTEGER NOT NULL DEFAULT 0,
    onboarding_day    INTEGER NOT NULL DEFAULT 0,          -- first-week DM step sent (0,1,3)
    rank_since        TEXT    NOT NULL DEFAULT (datetime('now')),
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Mirror of curriculum/*.yaml (loaded on start / /admin reload-curriculum). YAML is the source of truth.
CREATE TABLE IF NOT EXISTS quests (
    id                          TEXT PRIMARY KEY,
    track                       TEXT NOT NULL,
    rank                        INTEGER NOT NULL,
    subject                     TEXT,                      -- comma-joined subjects
    required_for_majors_json    TEXT NOT NULL DEFAULT '[]',
    taster_for_majors_json      TEXT NOT NULL DEFAULT '[]',
    adjacent_for_json           TEXT NOT NULL DEFAULT '[]',
    required_spine              INTEGER NOT NULL DEFAULT 0,
    elective                    INTEGER NOT NULL DEFAULT 0,
    capstone                    INTEGER NOT NULL DEFAULT 0,
    seal                        TEXT,
    title                       TEXT NOT NULL,
    body                        TEXT,
    time_min                    INTEGER,
    official_url                TEXT,
    backup_url                  TEXT,
    checklist_json              TEXT NOT NULL DEFAULT '[]',
    quiz_json                   TEXT NOT NULL DEFAULT '[]',
    done_when                   TEXT,
    xp                          INTEGER NOT NULL DEFAULT 0,
    next_hint                   TEXT,
    flavors_json                TEXT NOT NULL DEFAULT '{}',
    verify_type                 TEXT NOT NULL,
    action_key                  TEXT
);

CREATE TABLE IF NOT EXISTS quest_progress (
    user_id     INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
    quest_id    TEXT    NOT NULL,
    status      TEXT    NOT NULL,           -- started|quiz_passed|submitted|done|skipped
    quiz_passed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    PRIMARY KEY (user_id, quest_id)
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    quest_id    TEXT    NOT NULL,
    score       INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    passed      INTEGER NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS submissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
    quest_id    TEXT    NOT NULL,
    payload     TEXT    NOT NULL,           -- text + attachment URLs (json)
    status      TEXT    NOT NULL DEFAULT 'pending',  -- pending|pass|changes|fail
    route       TEXT    NOT NULL,           -- auto|honor|peer|mentor|human
    reviewer_id INTEGER,
    notes       TEXT,
    queue_message_id INTEGER,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    decided_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_sub_user_quest ON submissions(user_id, quest_id);
CREATE INDEX IF NOT EXISTS idx_sub_status ON submissions(status);

-- Each approve/verdict. Two peer approves at R3+ = pass.
CREATE TABLE IF NOT EXISTS review_actions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    reviewer_id   INTEGER NOT NULL,
    verdict       TEXT    NOT NULL,         -- pass|changes|fail|approve
    is_peer       INTEGER NOT NULL,
    notes         TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (submission_id, reviewer_id)
);

CREATE TABLE IF NOT EXISTS unlocks (
    key         TEXT PRIMARY KEY,           -- rank:0 .. rank:6, seal:design, major:level_design, oriented
    role_id     INTEGER,
    channel_ids TEXT NOT NULL DEFAULT '[]'  -- category or channel ids (json)
);

CREATE TABLE IF NOT EXISTS xp_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    amount      INTEGER NOT NULL,
    reason      TEXT    NOT NULL,           -- quest:S6 | quiz_bonus:S6 | peer_review:123 | showcase:thread | grant:by_id
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_xp_user_time ON xp_log(user_id, created_at);

CREATE TABLE IF NOT EXISTS medals (
    user_id     INTEGER NOT NULL,
    medal_key   TEXT    NOT NULL,
    earned_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, medal_key)
);

CREATE TABLE IF NOT EXISTS raids (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    quest_id    TEXT NOT NULL,
    host_id     INTEGER NOT NULL,
    starts_at   TEXT NOT NULL,
    ends_at     TEXT
);

-- Small flags: orientation sub-steps (used_rank/used_quest), skipped electives, etc.
CREATE TABLE IF NOT EXISTS kv (
    user_id     INTEGER NOT NULL,
    k           TEXT    NOT NULL,
    v           TEXT,
    PRIMARY KEY (user_id, k)
);
