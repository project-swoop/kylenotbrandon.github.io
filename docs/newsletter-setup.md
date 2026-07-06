# Newsletter setup (Google Apps Script)

Email subscribers when you publish a new post. The blog sends themed HTML mail and includes a one-click unsubscribe link.

## What lives in this repo

| File | Purpose |
|------|---------|
| `email/new-post.html` | XP-styled email template (edit freely) |
| `.github/newsletter/Code.gs` | Apps Script backend — copy into Google |
| `.github/scripts/notify_subscribers.py` | GitHub Action calls Apps Script after deploy |
| `.github/workflows/notify-subscribers.yml` | Runs after Pages deploy |
| `subscribe.md` | Reader signup form |
| `_config.yml` → `newsletter.apps_script_url` | Web app URL for the form |

## One-time setup (~15 minutes)

### 1. Create the subscriber spreadsheet

1. Open [Google Sheets](https://sheets.google.com) and create a blank spreadsheet (e.g. “Blog newsletter”).
2. Copy the **Sheet ID** from the URL:  
   `https://docs.google.com/spreadsheets/d/`**`SHEET_ID_HERE`**`/edit`

### 2. Create the Apps Script project

1. In the spreadsheet: **Extensions → Apps Script**.
2. Delete the default `Code.gs` content and paste everything from [`.github/newsletter/Code.gs`](../.github/newsletter/Code.gs).
3. Run **`setupSheet`** once from the editor (▶ Run). Approve permissions when prompted.
4. Open **Project settings → Script properties** and add:

| Property | Value |
|----------|--------|
| `SHEET_ID` | Your spreadsheet ID |
| `WEBHOOK_SECRET` | Long random string (e.g. `openssl rand -hex 32`) |
| `TEMPLATE_URL` | `https://raw.githubusercontent.com/project-swoop/kylenotbrandon.github.io/main/email/new-post.html` |
| `SITE_URL` | `https://kylenotbrandon.blog` |
| `SITE_TITLE` | `kyle speaks on...` |
| `SUBSCRIBE_REDIRECT` | `https://kylenotbrandon.blog/subscribe/?done=1` |
| `FROM_NAME` | `kyle speaks on...` |

### 3. Deploy the web app

1. **Deploy → New deployment → Web app**
2. **Execute as:** Me  
3. **Who has access:** Anyone  
4. Deploy and copy the **Web app URL** (ends with `/exec`).
5. Add script property **`WEB_APP_URL`** = that URL (same value you just copied).

### 4. Wire up the blog

1. In `_config.yml`, set `newsletter.apps_script_url` to your web app URL (replace `REPLACE_ME`).
2. Commit and push.

### 5. Add GitHub Actions secrets

In the repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|--------|--------|
| `NEWSLETTER_WEBHOOK_URL` | Same web app URL (`…/exec`) |
| `NEWSLETTER_WEBHOOK_SECRET` | Same string as `WEBHOOK_SECRET` in Apps Script |

## Test it

1. Visit [kylenotbrandon.blog/subscribe/](https://kylenotbrandon.blog/subscribe/) and sign up with your email.
2. Confirm the row appears in the **subscribers** sheet.
3. In GitHub: **Actions → Notify newsletter subscribers → Run workflow**, enable **force_latest**, run.
4. Check your inbox for the themed email.
5. Click **Unsubscribe** and confirm the `active` column becomes `FALSE`.

## How publishing works

1. You push a new file under `_posts/`.
2. **Deploy Jekyll site to Pages** builds and deploys.
3. **Notify newsletter subscribers** runs on success, detects the new post, and POSTs to Apps Script.
4. Apps Script fetches `email/new-post.html` from GitHub, fills in post details per subscriber, and sends via Gmail.

## Customizing the email

Edit `email/new-post.html` in this repo. Placeholders:

- `{{SITE_TITLE}}` `{{SITE_URL}}`
- `{{POST_TITLE}}` `{{POST_DATE}}` `{{POST_URL}}` `{{POST_EXCERPT}}`
- `{{UNSUBSCRIBE_URL}}` (per-subscriber; do not hardcode)

After you change the template, push to `main`. The next send fetches the updated file from the raw GitHub URL.

## Limits and notes

- **Gmail** (via Apps Script) allows about **500 emails/day** — plenty for a personal blog.
- The first time you send, Google may show a security review screen; approve it for your account.
- If secrets are missing, the notify workflow skips quietly (deploy still succeeds).
- Unsubscribe links go to your Apps Script web app with a unique token per subscriber. Gmail and Apple Mail also show a one-click **Unsubscribe** button via `List-Unsubscribe` headers.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Subscribe form shows “not configured” | Set `newsletter.apps_script_url` in `_config.yml` |
| No email after publish | Check Actions logs; verify secrets; run test workflow with **force_latest** |
| `unauthorized` in Action logs | `NEWSLETTER_WEBHOOK_SECRET` must match Apps Script `WEBHOOK_SECRET` |
| Template fetch failed | Confirm `TEMPLATE_URL` points at raw `main` on GitHub and the file is pushed |
| Permission denied in Apps Script | Re-run `setupSheet` and re-authorize Gmail + Sheets |
