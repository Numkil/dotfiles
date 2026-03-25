#!/usr/bin/env node

/**
 * Search for files by name within the project's Google Drive folder.
 * 
 * Usage: node search-files.mjs <query> [project_name]
 *   Defaults to cwd basename for project.
 *   Query is matched against file names (case-insensitive contains).
 * 
 * Output: JSON array of matching files.
 */

import { google } from 'googleapis';
import { getProjectFolderId } from './navigate.mjs';
import path from 'path';

async function searchInFolder(drive, folderId, query, currentPath = '') {
  const results = [];
  let pageToken = null;

  do {
    const res = await drive.files.list({
      q: `'${folderId}' in parents and trashed=false`,
      fields: 'nextPageToken, files(id, name, mimeType, modifiedTime, size)',
      pageSize: 100,
      pageToken,
      includeItemsFromAllDrives: true,
      supportsAllDrives: true,
    });

    for (const file of res.data.files || []) {
      const filePath = currentPath ? `${currentPath}/${file.name}` : file.name;

      if (file.name.toLowerCase().includes(query.toLowerCase())) {
        results.push({
          id: file.id,
          name: file.name,
          mimeType: file.mimeType,
          path: filePath,
          modifiedTime: file.modifiedTime,
          size: file.size,
        });
      }

      if (file.mimeType === 'application/vnd.google-apps.folder') {
        const subResults = await searchInFolder(drive, file.id, query, filePath);
        results.push(...subResults);
      }
    }

    pageToken = res.data.nextPageToken;
  } while (pageToken);

  return results;
}

const query = process.argv[2];
const projectName = process.argv[3] || path.basename(process.cwd());

if (!query) {
  console.error('Usage: node search-files.mjs <query> [project_name]');
  process.exit(1);
}

try {
  const { folderId, folderName, drive } = await getProjectFolderId(projectName);
  const files = await searchInFolder(drive, folderId, query);
  console.log(JSON.stringify({ project: folderName, query, matches: files }, null, 2));
} catch (e) {
  console.error(`Error: ${e.message}`);
  process.exit(1);
}
