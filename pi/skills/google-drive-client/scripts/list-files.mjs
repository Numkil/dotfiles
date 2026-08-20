#!/usr/bin/env node

/**
 * List all files in the project's Google Drive folder (recursive).
 * 
 * Usage: node list-files.mjs [project_name]
 *   Defaults to cwd basename (uppercased).
 * 
 * Output: JSON array of { id, name, mimeType, path, modifiedTime }
 */

import { google } from 'googleapis';
import { getProjectFolderId } from './navigate.mjs';
import path from 'path';

async function listAllFiles(drive, folderId, currentPath = '') {
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
      results.push({
        id: file.id,
        name: file.name,
        mimeType: file.mimeType,
        path: filePath,
        modifiedTime: file.modifiedTime,
        size: file.size,
      });

      if (file.mimeType === 'application/vnd.google-apps.folder') {
        const subFiles = await listAllFiles(drive, file.id, filePath);
        results.push(...subFiles);
      }
    }

    pageToken = res.data.nextPageToken;
  } while (pageToken);

  return results;
}

const projectName = process.argv[2] || path.basename(process.cwd());

try {
  const { folderId, folderName, drive } = await getProjectFolderId(projectName);
  const files = await listAllFiles(drive, folderId);
  console.log(JSON.stringify({ project: folderName, folderId, files }, null, 2));
} catch (e) {
  console.error(`Error: ${e.message}`);
  process.exit(1);
}
