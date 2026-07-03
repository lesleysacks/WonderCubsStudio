# AI Agents

AI providers are not integrated yet.

Sprint 3.4 prepares the input contract for future agents through the Workspace Context Engine. Agents should consume the structured JSON returned by `WorkspaceService.export_context()` instead of gathering project metadata independently.

Planned consumers:

- Story Agent
- Voice Agent
- Image Agent
- Thumbnail Agent
- SEO Agent

The exported context includes workspace identity, lesson/topic/language, platform, production format, style, current scene, status, and timestamps.
