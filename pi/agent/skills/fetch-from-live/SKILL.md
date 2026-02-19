---
name: fetch-from-live
description: Downloads files from Statik live project servers via SCP. Use when the user asks to fetch, download, or pull files from a live/production server. The project name is derived from the current working directory name and maps to a Statik hosting server.
---

# Fetch From Live

Downloads files from Statik live project servers. The current directory name determines which server to connect to.

## How It Works

The project name is taken from the current working directory (e.g. if you're in `~/Documents/projects/mysite`, the project is `mysite`). This maps to:

- **SSH host:** `<project>livestatikbe@<project>.ssh.statik.be`
- **Remote path:** `/data/sites/web/<project>livestatikbe/subsites/<project>.live.statik.be/current/<filename>`

SSH keys are pre-configured in `~/.ssh/config`.

## Usage

```bash
bash ~/.pi/agent/skills/fetch-from-live/fetch.sh <filename> [project-name]
```

- `<filename>` — File or directory to download (e.g. `.env`, `web/uploads/image.jpg`). Downloaded to the same relative path locally.
- `[project-name]` — Optional. Overrides the auto-detected project name from the current directory.

### Examples

```bash
# Download .env file (project name inferred from current directory)
bash ~/.pi/agent/skills/fetch-from-live/fetch.sh .env

# Download an uploads directory
bash ~/.pi/agent/skills/fetch-from-live/fetch.sh web/assets/uploads

# Specify project name explicitly
bash ~/.pi/agent/skills/fetch-from-live/fetch.sh .env myproject
```

## Important

- Always confirm with the user which file(s) they want before downloading.
- The user must be in the correct project directory (or provide the project name) for the server mapping to work.
- Uses `scp -r`, so directories are supported.
