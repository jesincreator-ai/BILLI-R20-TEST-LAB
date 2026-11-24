# BILLI R-20 — Free Drive-to-GitHub Automation

## Safety first
The BILLI-R20-TEST-LAB repository is currently public. **Do not export private Drive documents into it.** Create a separate PRIVATE repository for the knowledge transfer target, such as `billi-r20-private-knowledge`.

## Architecture (no business account required)
- Google Apps Script: scheduled Drive-folder scan and transfer.
- A separate private GitHub repository: stores exported text documents.
- GitHub Actions in this project: validates/builds a searchable index from only public-safe content committed here.
- Vercel: deploys the website when its connected GitHub repo changes.

## 1) Create a private knowledge repository
In GitHub, create a repository named `billi-r20-private-knowledge` and set **Private**. Initialize it with a README. Do not place secrets in either repository.

## 2) Create a fine-scoped GitHub token
In GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens:
- Repository access: only the private knowledge repository.
- Permissions: Contents — Read and write.
- Expiration: use a short period and renew when necessary.
Do not paste the token into ChatGPT, commit it, or put it in a source file.

## 3) Set up Google Apps Script
Open https://script.google.com, create a project, and paste the code from `scripts/drive_to_private_github.gs`.

In Apps Script → Project Settings → Script Properties, add:
- `DRIVE_FOLDER_ID`: ID of the Drive folder you want to sync (not your whole Drive).
- `GITHUB_TOKEN`: fine-grained token described above.
- `GITHUB_OWNER`: your GitHub username.
- `GITHUB_REPO`: private repository name.
- `GITHUB_BRANCH`: branch name (normally `main`).

Run `syncDriveFolderToPrivateGitHub` once and approve the requested Google Drive and external-request permissions. Review the execution log. The script checks that the destination repository is private and stops if it is public.

## 4) Schedule automation
Apps Script → Triggers → Add Trigger:
- Function: `syncDriveFolderToPrivateGitHub`
- Event source: Time-driven
- Frequency: every 15 minutes (or choose a less frequent schedule).

The script scans the selected folder and nested subfolders, and syncs supported text files and Google Docs. PDFs and unsupported formats are logged and skipped; they are not silently converted. You can add a PDF extraction/OCR step later.

## 5) Verify
- Add a test document to the designated Drive folder.
- Run the script once manually.
- Check the private repository's `drive-export/` folder.
- Then enable the schedule.

## Free-tier note
Google Apps Script and GitHub have usage quotas/limits. This setup is free within those limits, not unlimited. Apps Script triggers may be delayed and can fail on large files or quota limits.

## What the GitHub Actions workflow in this public repo does
It builds a local index from the public repository's `knowledge/public/` folder only. It does **not** read your private Drive or private knowledge repo. This is intentional.
