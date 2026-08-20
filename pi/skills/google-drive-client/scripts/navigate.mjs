/**
 * Navigate the Google Drive folder structure to find the project folder.
 * 
 * Path: "Statik" (shared) -> "Projects" -> "{first_letter}" -> "{PROJECT_NAME}"
 * 
 * Usage: node navigate.mjs [project_name]
 *   If no project_name given, derives from cwd basename (uppercased).
 */

import { google } from 'googleapis';
import { getAuthClient } from './auth.mjs';
import path from 'path';

async function findFolder(drive, name, parentId, shared = false) {
  const q = shared
    ? `name='${name}' and mimeType='application/vnd.google-apps.folder' and sharedWithMe`
    : `name='${name}' and mimeType='application/vnd.google-apps.folder' and '${parentId}' in parents and trashed=false`;

  const res = await drive.files.list({
    q,
    fields: 'files(id, name)',
    includeItemsFromAllDrives: true,
    supportsAllDrives: true,
  });

  if (!res.data.files || res.data.files.length === 0) {
    return null;
  }
  return res.data.files[0];
}

export async function getProjectFolderId(projectName) {
  const auth = await getAuthClient();
  const drive = google.drive({ version: 'v3', auth });

  // Step 1: Find "Statik" shared folder
  const statik = await findFolder(drive, 'Statik', null, true);
  if (!statik) throw new Error('Could not find shared folder "Statik"');

  // Step 2: Find "Projects" inside Statik
  const projects = await findFolder(drive, 'Projects', statik.id);
  if (!projects) throw new Error('Could not find "Projects" folder inside Statik');

  // Step 3: Find first-letter folder
  const letter = projectName.charAt(0).toUpperCase();
  const letterFolder = await findFolder(drive, letter, projects.id);
  if (!letterFolder) throw new Error(`Could not find letter folder "${letter}" inside Projects`);

  // Step 4: Find project folder (prefix match since Drive folders have descriptions appended)
  const upperName = projectName.toUpperCase();
  const projectRes = await drive.files.list({
    q: `name contains '${upperName}' and mimeType='application/vnd.google-apps.folder' and '${letterFolder.id}' in parents and trashed=false`,
    fields: 'files(id, name)',
    includeItemsFromAllDrives: true,
    supportsAllDrives: true,
  });
  const projectFolder = (projectRes.data.files || []).find(f => f.name.startsWith(upperName));
  if (!projectFolder) throw new Error(`Could not find project folder starting with "${upperName}" inside ${letter}`);

  return { folderId: projectFolder.id, folderName: projectFolder.name, drive };
}

// CLI entry point
if (process.argv[1] && process.argv[1].includes('navigate.mjs')) {
  const projectName = process.argv[2] || path.basename(process.cwd());
  try {
    const { folderId, folderName } = await getProjectFolderId(projectName);
    console.log(JSON.stringify({ folderId, folderName }));
  } catch (e) {
    console.error(e.message);
    process.exit(1);
  }
}
