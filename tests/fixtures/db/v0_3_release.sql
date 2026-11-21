-- v0.3 hardening: lifecycle columns, auto-created workspaces
-- Schema created by initialize_database() at commit 7aa2f8b.
-- Regenerate with tests/fixtures/db/build_fixtures.py
BEGIN TRANSACTION;
CREATE TABLE Characters (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    gender TEXT NOT NULL,
    age_group TEXT NOT NULL,
    fur_color TEXT NOT NULL,
    mane_color TEXT NOT NULL,
    eye_color TEXT NOT NULL,
    shirt TEXT NOT NULL,
    pants TEXT NOT NULL,
    shoes TEXT NOT NULL,
    accessories TEXT NOT NULL,
    personality TEXT NOT NULL,
    voice_style TEXT NOT NULL,
    catchphrase TEXT NOT NULL,
    description TEXT NOT NULL,
    image_folder TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
INSERT INTO "Characters" VALUES('c-leo','Leo','Lion','','','','','','','','','','Curious','','Let''s go! ¡Vamos!','','','2026-07-01 10:00:00','2026-07-02 10:00:00');
INSERT INTO "Characters" VALUES('c-zoe','Zoë','Fox','','','','','','','','','','Curious','','Let''s go! ¡Vamos!','','','2026-07-01 10:00:00','2026-07-02 10:00:00');
CREATE TABLE Goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_date TEXT NOT NULL,
    description TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "Goals" VALUES(1,'2026-06-30','Finish Leo storyboard',1,'2026-06-30 08:00:00');
INSERT INTO "Goals" VALUES(2,'2026-07-01','Record voice — 第一話',0,'2026-07-01 08:00:00');
CREATE TABLE Projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    lesson TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TEXT,
    folder_path TEXT NOT NULL
);
INSERT INTO "Projects" VALUES(1,'001','Leo Learns Colors','Colors','In Progress','2026-06-30 10:00:00','2026-06-30 10:00:00',NULL,'C:\Users\Creator\WonderCubs Studio\projects\001_Leo_Learns_Colors');
INSERT INTO "Projects" VALUES(2,'002','Café Été — 日本語','Seasons','Published','2026-06-30 11:00:00','2026-06-30 11:00:00','2026-06-30 11:00:00','C:\Users\Creator\WonderCubs Studio\projects\002_Caf_t');
INSERT INTO "Projects" VALUES(3,'003','Intro','Hello','Review','2026-08-01 09:00:00','2026-08-01 09:00:00',NULL,'C:\Users\Creator\WonderCubs Studio\projects\003_Intro');
INSERT INTO "Projects" VALUES(4,'004','Intro','Goodbye','Draft','2026-08-01 09:05:00','2026-08-01 09:05:00',NULL,'C:\Users\Creator\WonderCubs Studio\projects\004_Intro');
INSERT INTO "Projects" VALUES(5,'005','Alpha','Letters','In Production','2026-08-02 12:00:00','2026-08-03 08:00:00',NULL,'C:\Users\Creator\WonderCubs Studio\projects\005_Alpha');
CREATE TABLE Prompts (
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    version INTEGER NOT NULL,
    description TEXT NOT NULL,
    template TEXT NOT NULL,
    variables TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    PRIMARY KEY (id, version)
);
INSERT INTO "Prompts" VALUES('p-story','Story Opener','Story',1,'First draft','Once upon a time {{CHARACTER_NAME}}','["CHARACTER_NAME"]','2026-07-22 10:00:00','2026-07-22 10:00:00',0);
INSERT INTO "Prompts" VALUES('p-story','Story Opener','Story',2,'Revised','Today {{CHARACTER_NAME}} learns {{LESSON}}','["CHARACTER_NAME", "LESSON"]','2026-07-22 10:00:00','2026-07-23 10:00:00',1);
INSERT INTO "Prompts" VALUES('p-seo','SEO Title — 日本','SEO',1,'','{{PROJECT_NAME}} | WonderCubs','["PROJECT_NAME"]','2026-07-22 11:00:00','2026-07-22 11:00:00',1);
CREATE TABLE Workspaces (
    uuid TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    lesson TEXT NOT NULL,
    topic TEXT NOT NULL,
    language TEXT NOT NULL,
    target_platform TEXT NOT NULL,
    resolution TEXT NOT NULL,
    aspect_ratio TEXT NOT NULL,
    duration INTEGER NOT NULL,
    style TEXT NOT NULL,
    current_scene TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
INSERT INTO "Workspaces" VALUES('w-leo','Leo Learns Colors','Colors','Leo Learns Colors','English','YouTube','1920x1080','16:9',60,'Pastel','Scene 1','In Progress','2026-06-30 10:00:00','2026-06-30 10:00:00');
INSERT INTO "Workspaces" VALUES('w-cafe','Café Été — 日本語','Seasons','Café Été — 日本語','English','YouTube','1920x1080','16:9',60,'Pastel','Scene 1','Published','2026-06-30 11:00:00','2026-06-30 11:00:00');
INSERT INTO "Workspaces" VALUES('w-intro-1','Intro','Hello','Intro','English','YouTube','1920x1080','16:9',60,'Pastel','Scene 1','Review','2026-08-01 09:00:00','2026-08-01 09:00:00');
INSERT INTO "Workspaces" VALUES('w-intro-2','Intro','Goodbye','Intro','English','YouTube','1920x1080','16:9',60,'Pastel','Scene 1','Draft','2026-08-01 09:05:00','2026-08-01 09:05:00');
INSERT INTO "Workspaces" VALUES('w-alpha','Alpha v2','Letters','Alpha v2','English','YouTube','1920x1080','16:9',60,'Pastel','Scene 1','In Production','2026-08-02 12:00:00','2026-08-03 08:00:00');
INSERT INTO "Workspaces" VALUES('w-ideas','Unrelated Ideas','Misc','Unrelated Ideas','English','TikTok','1920x1080','16:9',60,'Pastel','Scene 1','Draft','2026-08-05 10:10:00','2026-08-05 10:10:00');
CREATE INDEX idx_goals_goal_date ON Goals (goal_date);
CREATE INDEX idx_characters_name ON Characters (name);
CREATE INDEX idx_workspaces_project_name ON Workspaces (project_name);
CREATE INDEX idx_prompts_name ON Prompts (name COLLATE NOCASE);
CREATE UNIQUE INDEX idx_prompts_one_active_version
ON Prompts (id) WHERE active = 1;
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('Projects',5);
INSERT INTO "sqlite_sequence" VALUES('Goals',2);
COMMIT;
