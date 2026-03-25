---
name: google-drive-client
description: Access client project files from Google Drive. Reads documents, spreadsheets, PDFs, and transcripts from the shared "Statik" folder structure (Statik > Projects > {Letter} > {PROJECT}). Use when the user asks about client context, project communications, meeting notes, transcripts, or any information that lives in Google Drive for the current project.
---

# Google Drive Client Context

Read files from the shared "Statik" Google Drive folder to answer questions about client projects.

## Folder Structure

```
Statik (shared) / Projects / {First Letter} / {PROJECT_NAME} / ...
```

The project name is derived from the current working directory basename (uppercased).
For example, if cwd is `/Users/merel/Documents/projects/chiweb`, the Drive path is:
`Statik > Projects > C > CHIWEB`

## Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project (or use an existing one)
3. Enable the **Google Drive API**
4. Create an **OAuth 2.0 Client ID** (type: Desktop app)
5. Download the credentials JSON and save it as:
   ```
   ~/.pi/agent/skills/google-drive-client/config/credentials.json
   ```
6. Install dependencies:
   ```bash
   cd ~/.pi/agent/skills/google-drive-client && npm install
   ```
7. Run any command once to complete the OAuth flow (it will open a URL to authorize):
   ```bash
   cd ~/.pi/agent/skills/google-drive-client && node scripts/list-files.mjs
   ```

## Usage

All scripts are in the skill directory. Always `cd` to the skill dir first or use absolute paths.

### List all files in the project folder

```bash
cd ~/.pi/agent/skills/google-drive-client && node scripts/list-files.mjs
```

This returns a JSON listing of all files with their `id`, `name`, `mimeType`, `path`, and `modifiedTime`. Use this first to discover what files are available.

### Search for files by name

```bash
cd ~/.pi/agent/skills/google-drive-client && node scripts/search-files.mjs "transcript"
cd ~/.pi/agent/skills/google-drive-client && node scripts/search-files.mjs "budget"
```

### Read a specific file's content

```bash
cd ~/.pi/agent/skills/google-drive-client && node scripts/read-file.mjs <file_id>
```

The `file_id` comes from the list or search output. Supported formats:
- **Google Docs** → plain text
- **Google Sheets** → CSV
- **Google Slides** → plain text
- **.docx** → plain text
- **.xlsx / .xls** → CSV per sheet
- **.pdf** → extracted text
- **Plain text / CSV / Markdown / JSON** → raw content

## Workflow

When the user asks a question about client context:

1. **List files** to see what's available in the project folder
2. **Search** if looking for something specific (e.g., "transcript", "budget", "brief")
3. **Read** the relevant file(s) by their ID
4. **Synthesize** the content to answer the user's question

Always tell the user which files you're reading from so they know the source.
