-- Release v0.2.0: + Goals
-- Schema created by initialize_database() at commit cbecf37.
-- Regenerate with tests/fixtures/db/build_fixtures.py
BEGIN TRANSACTION;
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
CREATE INDEX idx_goals_goal_date ON Goals (goal_date);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('Projects',3);
INSERT INTO "sqlite_sequence" VALUES('Goals',2);
COMMIT;
