/**
 * Google Drive OAuth2 authentication helper.
 * 
 * First run: generates an auth URL, you visit it, paste the code back.
 * Subsequent runs: uses the stored refresh token.
 * 
 * Credentials and tokens are stored in ~/.pi/agent/skills/google-drive-client/config/
 */

import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import readline from 'readline';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_DIR = path.join(__dirname, '..', 'config');
const CREDENTIALS_PATH = path.join(CONFIG_DIR, 'credentials.json');
const TOKEN_PATH = path.join(CONFIG_DIR, 'token.json');

const SCOPES = ['https://www.googleapis.com/auth/drive.readonly'];

export async function getAuthClient() {
  if (!fs.existsSync(CREDENTIALS_PATH)) {
    throw new Error(
      `Missing credentials.json in ${CONFIG_DIR}\n` +
      `Go to https://console.cloud.google.com/apis/credentials\n` +
      `Create an OAuth 2.0 Client ID (Desktop app), download the JSON,\n` +
      `and save it as ${CREDENTIALS_PATH}`
    );
  }

  const content = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'));
  const { client_id, client_secret } = content.installed || content.web;
  const oauth2Client = new google.auth.OAuth2(client_id, client_secret, 'http://localhost:3847');

  if (fs.existsSync(TOKEN_PATH)) {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
    oauth2Client.setCredentials(token);
    
    // Check if token needs refresh
    if (token.expiry_date && token.expiry_date < Date.now()) {
      try {
        const { credentials } = await oauth2Client.refreshAccessToken();
        oauth2Client.setCredentials(credentials);
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(credentials, null, 2));
      } catch (e) {
        // Token refresh failed, need to re-auth
        fs.unlinkSync(TOKEN_PATH);
        return getAuthClient();
      }
    }
    return oauth2Client;
  }

  // Interactive auth flow
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent',
  });

  console.log(`\nAuthorize this app by visiting:\n\n${authUrl}\n`);

  const rl = readline.createInterface({ input: process.stdin, output: process.stderr });
  const code = await new Promise(resolve => {
    rl.question('Paste the authorization code here: ', answer => {
      rl.close();
      resolve(answer.trim());
    });
  });

  const { tokens } = await oauth2Client.getToken(code);
  oauth2Client.setCredentials(tokens);

  if (!fs.existsSync(CONFIG_DIR)) fs.mkdirSync(CONFIG_DIR, { recursive: true });
  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));
  console.error('Token stored successfully.');

  return oauth2Client;
}
