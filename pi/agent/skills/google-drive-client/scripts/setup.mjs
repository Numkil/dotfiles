#!/usr/bin/env node

/**
 * Standalone OAuth setup script. Run this directly in your terminal:
 *   cd ~/.pi/agent/skills/google-drive-client && node scripts/setup.mjs
 * 
 * It starts a tiny local HTTP server to catch the OAuth redirect automatically.
 */

import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';
import { URL } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_DIR = path.join(__dirname, '..', 'config');
const CREDENTIALS_PATH = path.join(CONFIG_DIR, 'credentials.json');
const TOKEN_PATH = path.join(CONFIG_DIR, 'token.json');

const SCOPES = ['https://www.googleapis.com/auth/drive.readonly'];
const PORT = 3847;

const content = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'));
const { client_id, client_secret } = content.installed || content.web;
const oauth2Client = new google.auth.OAuth2(client_id, client_secret, `http://localhost:${PORT}`);

const authUrl = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  scope: SCOPES,
  prompt: 'consent',
});

console.log(`\n🔑 Opening authorization URL in your browser...\n`);
console.log(`If it doesn't open automatically, visit:\n${authUrl}\n`);

// Try to open the URL
import('child_process').then(cp => {
  cp.exec(`open "${authUrl}"`);
});

// Start a temporary server to catch the redirect
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const code = url.searchParams.get('code');

  if (code) {
    try {
      const { tokens } = await oauth2Client.getToken(code);
      if (!fs.existsSync(CONFIG_DIR)) fs.mkdirSync(CONFIG_DIR, { recursive: true });
      fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));

      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end('<html><body><h1>✅ Authorized!</h1><p>You can close this tab and go back to your terminal.</p></body></html>');
      console.log('✅ Token saved successfully! You can now use the Google Drive skill.');
      server.close();
      process.exit(0);
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'text/html' });
      res.end(`<html><body><h1>❌ Error</h1><pre>${e.message}</pre></body></html>`);
      console.error('Error:', e.message);
      server.close();
      process.exit(1);
    }
  } else {
    res.writeHead(400, { 'Content-Type': 'text/html' });
    res.end('<html><body><h1>❌ No code received</h1></body></html>');
  }
});

server.listen(PORT, () => {
  console.log(`Waiting for authorization on http://localhost:${PORT} ...\n`);
});

// Timeout after 2 minutes
setTimeout(() => {
  console.error('Timed out waiting for authorization.');
  server.close();
  process.exit(1);
}, 120000);
