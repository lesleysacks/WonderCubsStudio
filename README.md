# WonderCubs Studio

WonderCubs Studio v0.1 is a desktop application for managing an AI-assisted YouTube production pipeline for a preschool educational channel.

## Project Overview

The app helps organize every video into a consistent production folder structure, stores project metadata in SQLite, and provides simple screens for creating projects, opening project folders, viewing the video queue, and editing core settings.

## Features

- Home screen for the main production workflow
- New project creation with video title, lesson, and video number
- Automatic project folder generation
- Placeholder production files for story, voice, prompts, thumbnail, SEO, notes, and README content
- SQLite project database
- Open existing project folders in Windows Explorer
- Video queue table
- JSON-backed settings screen
- Application logging to `logs/app.log`
- Modular Python architecture

## Installation

1. Install Python 3.13 or newer.
2. Open this folder in VS Code.
3. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

5. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

6. Run the app:

   ```powershell
   python app.py
   ```

## Requirements

- Windows 11
- Python 3.13+
- CustomTkinter
- SQLite, included with Python

## Folder Structure

```text
WonderCubsStudio/
├── app.py
├── requirements.txt
├── README.md
├── config.json
├── database.db
├── assets/
├── data/
├── logs/
├── projects/
├── templates/
├── src/
│   ├── ui/
│   ├── database/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── controllers/
└── tests/
```

## Future Roadmap

### Version 0.2

- Character Manager
- Prompt Library

### Version 0.3

- Voice Manager
- Image Generator
- Analytics Dashboard

### Version 1.0

- AI Agent Integration
- YouTube API
- One-click Production Pipeline

## License

This project is provided as an internal production tool. Add a formal license before public distribution.
