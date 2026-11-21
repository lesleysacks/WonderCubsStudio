-- Sprint 3.4: + Characters, manually created Workspaces
-- Schema created by initialize_database() at commit 6c95a42.
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
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    folder_path TEXT NOT NULL
);
INSERT INTO "Projects" VALUES(1,'001','Leo Learns Colors','Colors','In Progress','2026-06-30 10:00:00','C:\Users\Creator\WonderCubs Studio\projects\001_Leo_Learns_Colors');
INSERT INTO "Projects" VALUES(2,'002','Café Été — 日本語','Seasons','Completed','2026-06-30 11:00:00','C:\Users\Creator\WonderCubs Studio\projects\002_Caf_t');
INSERT INTO "Projects" VALUES(3,'003','Shapes','Shapes','Uploaded','2026-07-01 09:00:00','C:\Users\Creator\WonderCubs Studio\projects\003_Shapes');
INSERT INTO "Projects" VALUES(4,'004','Intro','Hello','In Progress','2026-07-03 09:00:00','C:\Users\Creator\WonderCubs Studio\projects\004_Intro');
INSERT INTO "Projects" VALUES(5,'005','Intro','Goodbye','In Progress','2026-07-03 09:05:00','C:\Users\Creator\WonderCubs Studio\projects\005_Intro');
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
INSERT INTO "Workspaces" VALUES('w-leo','Leo Learns Colors','Colors','Leo Learns Colors','English','YouTube','1920x1080','16:9',60,'Pastel','Scene 1','In Progress','2026-07-03 10:00:00','2026-07-03 10:00:00');
INSERT INTO "Workspaces" VALUES('w-intro','Intro','Hello','Intro','English','YouTube','1920x1080','16:9',60,'Pastel','Scene 1','Ready','2026-07-03 10:05:00','2026-07-03 10:05:00');
INSERT INTO "Workspaces" VALUES('w-ideas','Unrelated Ideas','Misc','Unrelated Ideas','English','TikTok','1920x1080','16:9',60,'Pastel','Scene 1','Draft','2026-07-03 10:10:00','2026-07-03 10:10:00');
CREATE INDEX idx_goals_goal_date ON Goals (goal_date);
CREATE INDEX idx_characters_name ON Characters (name);
CREATE INDEX idx_workspaces_project_name ON Workspaces (project_name);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('Projects',5);
INSERT INTO "sqlite_sequence" VALUES('Goals',2);
COMMIT;
