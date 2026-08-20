#!/usr/bin/env node

/**
 * Read the content of a file from Google Drive by file ID.
 * 
 * Usage: node read-file.mjs <file_id>
 * 
 * Supports:
 *   - Google Docs -> plain text
 *   - Google Sheets -> CSV (all sheets)
 *   - Google Slides -> plain text
 *   - .docx -> plain text (via mammoth)
 *   - .xlsx/.xls -> CSV (via xlsx)
 *   - .pdf -> text (via pdf-parse)
 *   - Plain text files -> raw content
 *   - .csv -> raw content
 */

import { google } from 'googleapis';
import { getAuthClient } from './auth.mjs';
import { Readable } from 'stream';
import mammoth from 'mammoth';
import XLSX from 'xlsx';
import pdf from 'pdf-parse';

async function streamToBuffer(stream) {
  const chunks = [];
  for await (const chunk of stream) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

async function readGoogleDoc(drive, fileId) {
  const res = await drive.files.export({
    fileId,
    mimeType: 'text/plain',
  }, { responseType: 'text' });
  return res.data;
}

async function readGoogleSheet(drive, fileId) {
  const res = await drive.files.export({
    fileId,
    mimeType: 'text/csv',
  }, { responseType: 'text' });
  return res.data;
}

async function readGoogleSlides(drive, fileId) {
  const res = await drive.files.export({
    fileId,
    mimeType: 'text/plain',
  }, { responseType: 'text' });
  return res.data;
}

async function downloadFile(drive, fileId) {
  const res = await drive.files.get({
    fileId,
    alt: 'media',
    supportsAllDrives: true,
  }, { responseType: 'stream' });
  return streamToBuffer(res.data);
}

async function readFileContent(drive, fileId, mimeType, fileName) {
  // Google Workspace types
  if (mimeType === 'application/vnd.google-apps.document') {
    return await readGoogleDoc(drive, fileId);
  }
  if (mimeType === 'application/vnd.google-apps.spreadsheet') {
    return await readGoogleSheet(drive, fileId);
  }
  if (mimeType === 'application/vnd.google-apps.presentation') {
    return await readGoogleSlides(drive, fileId);
  }

  // Download the binary file
  const buffer = await downloadFile(drive, fileId);

  // Word documents
  if (mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
      fileName?.endsWith('.docx')) {
    const result = await mammoth.extractRawText({ buffer });
    return result.value;
  }

  // Excel files
  if (mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      mimeType === 'application/vnd.ms-excel' ||
      fileName?.endsWith('.xlsx') || fileName?.endsWith('.xls')) {
    const workbook = XLSX.read(buffer, { type: 'buffer' });
    const sheets = [];
    for (const sheetName of workbook.SheetNames) {
      const csv = XLSX.utils.sheet_to_csv(workbook.Sheets[sheetName]);
      sheets.push(`=== Sheet: ${sheetName} ===\n${csv}`);
    }
    return sheets.join('\n\n');
  }

  // PDF
  if (mimeType === 'application/pdf' || fileName?.endsWith('.pdf')) {
    const data = await pdf(buffer);
    return data.text;
  }

  // Plain text, CSV, markdown, etc.
  const textTypes = [
    'text/', 'application/json', 'application/xml', 'application/csv',
    'application/javascript', 'application/x-yaml',
  ];
  if (textTypes.some(t => mimeType?.startsWith(t)) ||
      /\.(txt|csv|md|json|xml|yaml|yml|html|htm|log|rtf)$/i.test(fileName)) {
    return buffer.toString('utf-8');
  }

  return `[Binary file: ${mimeType}, ${buffer.length} bytes - content cannot be displayed as text]`;
}

// CLI entry
const fileId = process.argv[2];
if (!fileId) {
  console.error('Usage: node read-file.mjs <file_id>');
  process.exit(1);
}

try {
  const auth = await getAuthClient();
  const drive = google.drive({ version: 'v3', auth });

  // Get file metadata first
  const meta = await drive.files.get({
    fileId,
    fields: 'id, name, mimeType',
    supportsAllDrives: true,
  });

  const { name, mimeType } = meta.data;
  console.error(`Reading: ${name} (${mimeType})`);

  const content = await readFileContent(drive, fileId, mimeType, name);
  console.log(content);
} catch (e) {
  console.error(`Error: ${e.message}`);
  process.exit(1);
}
