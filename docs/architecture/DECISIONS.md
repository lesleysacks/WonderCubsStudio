# ADR-001 - Repository Pattern

Status: Accepted

Decision:
Use the Repository Pattern to isolate database access from business logic.

Reason:
Allows SQLite to be replaced with PostgreSQL in the future without changing services or UI.

Consequences:
- Cleaner architecture
- Easier testing
- Better scalability