/**
 * BILLI Drive -> PRIVATE GitHub knowledge transfer.
 * Configure Script Properties before running:
 * DRIVE_FOLDER_ID, GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH (optional).
 * This script refuses to sync unless GitHub confirms the destination is private.
 * Supported: Google Docs, TXT, Markdown, CSV, JSON.
 * Unsupported files (including PDFs) are skipped and logged.
 */
function syncDriveFolderToPrivateGitHub() {
  const props = PropertiesService.getScriptProperties();
  const folderId = requiredProperty_(props, 'DRIVE_FOLDER_ID');
  const token = requiredProperty_(props, 'GITHUB_TOKEN');
  const owner = requiredProperty_(props, 'GITHUB_OWNER');
  const repo = requiredProperty_(props, 'GITHUB_REPO');
  const branch = props.getProperty('GITHUB_BRANCH') || 'main';

  const repoInfo = githubRequest_(token, 'GET', 'https://api.github.com/repos/' + encodeURIComponent(owner) + '/' + encodeURIComponent(repo));
  if (repoInfo.private !== true) {
    throw new Error('SAFETY STOP: destination GitHub repository is not private. No Drive files were transferred.');
  }

  const folder = DriveApp.getFolderById(folderId);
  const iterator = folder.getFiles();
  let transferred = 0, skipped = 0, failed = 0;

  while (iterator.hasNext()) {
    const file = iterator.next();
    try {
      const mime = file.getMimeType();
      const name = file.getName();
      const fileId = file.getId();
      let textContent;

      if (mime === MimeType.GOOGLE_DOCS) {
        const exportUrl = 'https://www.googleapis.com/drive/v3/files/' + encodeURIComponent(fileId) + '/export?mimeType=text%2Fplain';
        const response = UrlFetchApp.fetch(exportUrl, {
          method: 'get',
          headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() },
          muteHttpExceptions: true
        });
        if (response.getResponseCode() >= 300) throw new Error('Google Docs export failed (' + response.getResponseCode() + ')');
        textContent = response.getContentText();
      } else if (mime === MimeType.PLAIN_TEXT || mime === 'text/markdown' || mime === 'text/csv' || mime === 'application/json') {
        textContent = file.getBlob().getDataAsString('UTF-8');
      } else {
        Logger.log('SKIPPED unsupported format: ' + name + ' (' + mime + ')');
        skipped++;
        continue;
      }

      const safeName = name.replace(/[^a-zA-Z0-9._-]+/g, '_').replace(/^\.+/, '').slice(0, 120) || 'document';
      const path = 'drive-export/' + safeName + '--' + fileId + '.txt';
      const contentBase64 = Utilities.base64Encode(textContent, Utilities.Charset.UTF_8);
      const existing = githubRequest_(token, 'GET', 'https://api.github.com/repos/' + owner + '/' + repo + '/contents/' + encodeURIComponent(path).replace(/%2F/g, '/') + '?ref=' + encodeURIComponent(branch), true);

      if (existing && existing.content) {
        const current = Utilities.newBlob(Utilities.base64Decode(existing.content.replace(/\n/g, ''))).getDataAsString('UTF-8');
        if (current === textContent) {
          Logger.log('UNCHANGED: ' + name);
          skipped++;
          continue;
        }
      }

      const payload = {
        message: 'Sync Drive file: ' + name,
        content: contentBase64,
        branch: branch
      };
      if (existing && existing.sha) payload.sha = existing.sha;
      githubRequest_(token, 'PUT', 'https://api.github.com/repos/' + owner + '/' + repo + '/contents/' + encodeURIComponent(path).replace(/%2F/g, '/'), payload);
      transferred++;
      Logger.log('TRANSFERRED: ' + name);
    } catch (err) {
      failed++;
      Logger.log('FAILED: ' + file.getName() + ' — ' + err.message);
    }
  }
  Logger.log('BILLI sync complete. Transferred=' + transferred + ', skipped=' + skipped + ', failed=' + failed);
}

function requiredProperty_(props, key) {
  const value = props.getProperty(key);
  if (!value) throw new Error('Missing Script Property: ' + key);
  return value;
}

function githubRequest_(token, method, url, payload, allowNotFound) {
  const options = {
    method: method,
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    muteHttpExceptions: true
  };
  if (payload && typeof payload === 'object') options.payload = JSON.stringify(payload);
  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  if (allowNotFound && code === 404) return null;
  if (code < 200 || code >= 300) throw new Error('GitHub API ' + method + ' failed (' + code + '): ' + response.getContentText().slice(0, 400));
  return response.getContentText() ? JSON.parse(response.getContentText()) : {};
}
