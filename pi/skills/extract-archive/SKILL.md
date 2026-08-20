---
name: extract-archive
description: Extracts archive files regardless of format. Supports tar.gz, gz, tar, tgz, tar.bz2, bz2, tar.xz, xz, tar.zst, zst, rar, tbz2, zip, Z, and 7z. Use when the user asks to extract, unpack, decompress, or unzip an archive file.
---

# Extract Archive

Extracts an archive file by detecting its extension and using the appropriate command.

## Usage

Given an archive file path from the user, run the matching command based on its extension.

**Important:** Match multi-extension patterns (e.g. `.tar.gz`) before single-extension patterns (e.g. `.gz`) to avoid incorrect matches. Extension matching is case-insensitive.

| Extension   | Command                   |
|-------------|---------------------------|
| `.tar.gz`   | `tar xzf <file>`          |
| `.tar.bz2`  | `tar xjf <file>`          |
| `.tar.xz`   | `tar xJf <file>`          |
| `.tar.zst`  | `tar --zstd -xf <file>`   |
| `.tbz2`     | `tar xjf <file>`          |
| `.tgz`      | `tar xzf <file>`          |
| `.gz`       | `gunzip <file>`           |
| `.bz2`      | `bunzip2 <file>`          |
| `.xz`       | `unxz <file>`             |
| `.zst`      | `unzstd <file>`           |
| `.tar`      | `tar xf <file>`           |
| `.rar`      | `unrar x <file>`          |
| `.zip`      | `unzip <file>`            |
| `.Z`        | `uncompress <file>`       |
| `.7z`       | `7z x <file>`             |

## Instructions

1. Verify the file exists before attempting extraction.
2. Match the file extension case-insensitively to determine the correct command.
3. Run the extraction command using `bash`.
4. If the extension is not recognized, tell the user the format is not supported.
5. If the user wants to extract to a specific directory, add `-C <dir>` for tar commands, `-d <dir>` for unzip, or `cd <dir> &&` as appropriate.
