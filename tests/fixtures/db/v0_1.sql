-- Initial release v0.1: Projects only
-- Schema created by initialize_database() at commit 0190936.
-- Regenerate with tests/fixtures/db/build_fixtures.py
BEGIN TRANSACTION;
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
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('Projects',3);
COMMIT;
