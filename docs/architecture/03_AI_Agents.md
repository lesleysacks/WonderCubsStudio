# AI Agents

AI providers and the AI Agent Engine are not part of v0.3. The engine is planned only after v0.4 establishes reliable image and voice asset management.

Sprint 3.4 prepares the input contract for future agents through the Workspace Context Engine. Agents should consume the structured JSON returned by `WorkspaceService.export_context()` instead of gathering project metadata independently.

Planned consumers:

- Story Agent
- Voice Agent
- Image Agent
- Thumbnail Agent
- SEO Agent

The exported context includes workspace identity, lesson/topic/language, platform, production format, style, current scene, status, and timestamps.
