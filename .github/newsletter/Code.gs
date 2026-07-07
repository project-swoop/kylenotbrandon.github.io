/**
 * kylenotbrandon.blog — newsletter backend (Google Apps Script)
 *
 * Deploy: Extensions → Apps Script → paste this file → Deploy → New deployment
 * Type: Web app — Execute as: Me — Who has access: Anyone
 *
 * Set Script properties (Project settings → Script properties):
 *   SHEET_ID           — Google Sheet ID for subscribers
 *   WEBHOOK_SECRET     — shared secret for GitHub Actions (random string)
 *   TEMPLATE_URL       — raw GitHub URL to email/new-post.html
 *   WEB_APP_URL        — deployed web app URL (ends with /exec)
 *   SITE_URL           — https://kylenotbrandon.blog
 *   SITE_TITLE         — kyle speaks on...
 *   SUBSCRIBE_REDIRECT — optional legacy; subscribe stays on the blog now
 *   FROM_NAME          — kyle speaks on...
 */

var PROPS = PropertiesService.getScriptProperties();

function getConfig() {
  return {
    sheetId: PROPS.getProperty('SHEET_ID'),
    webhookSecret: PROPS.getProperty('WEBHOOK_SECRET'),
    siteUrl: PROPS.getProperty('SITE_URL') || 'https://kylenotbrandon.blog',
    siteTitle: PROPS.getProperty('SITE_TITLE') || 'kyle speaks on...',
    templateUrl: PROPS.getProperty('TEMPLATE_URL'),
    subscribeRedirect: PROPS.getProperty('SUBSCRIBE_REDIRECT') || 'https://kylenotbrandon.blog/subscribe/?done=1',
    fromName: PROPS.getProperty('FROM_NAME') || 'kyle speaks on...',
    webAppUrl: PROPS.getProperty('WEB_APP_URL') || ScriptApp.getService().getUrl(),
  };
}

function getSheet() {
  var cfg = getConfig();
  if (!cfg.sheetId) {
    throw new Error('SHEET_ID script property is not set.');
  }
  var ss = SpreadsheetApp.openById(cfg.sheetId);
  var sheet = ss.getSheetByName('subscribers');
  if (!sheet) {
    sheet = ss.insertSheet('subscribers');
    sheet.appendRow(['email', 'token', 'subscribed_at', 'active']);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function generateToken() {
  return Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '').slice(0, 8);
}

function normalizeEmail(email) {
  return String(email || '').trim().toLowerCase();
}

function isActive(value) {
  return value === true || value === 'TRUE' || value === 1 || value === '1';
}

function doGet(e) {
  var params = e && e.parameter ? e.parameter : {};
  var action = String(params.action || '').toLowerCase();

  if (action === 'unsubscribe') {
    return handleUnsubscribe(params.token);
  }

  return HtmlService.createHtmlOutput(
    wrapPage('Newsletter', '<p>Newsletter service is running.</p>')
  );
}

function doPost(e) {
  var params = e && e.parameter ? e.parameter : {};
  var action = String(params.action || '').toLowerCase();

  if (action === 'unsubscribe') {
    return handleUnsubscribePost(params.token);
  }

  if (action === 'subscribe') {
    return handleSubscribe(params.email);
  }

  var body = {};
  if (e && e.postData && e.postData.contents) {
    try {
      body = JSON.parse(e.postData.contents);
    } catch (err) {
      return jsonResponse({ ok: false, error: 'invalid json' });
    }
  }

  if (body.action === 'send') {
    return handleSend(body);
  }

  return jsonResponse({ ok: false, error: 'unknown action' });
}

function handleSubscribe(email) {
  email = normalizeEmail(email);
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return HtmlService.createHtmlOutput('<!DOCTYPE html><html><body>invalid</body></html>');
  }

  var sheet = getSheet();
  var data = sheet.getDataRange().getValues();

  for (var i = 1; i < data.length; i++) {
    if (normalizeEmail(data[i][0]) !== email) {
      continue;
    }
    if (isActive(data[i][3])) {
      return subscribeAck();
    }
    var token = data[i][1] || generateToken();
    sheet.getRange(i + 1, 2).setValue(token);
    sheet.getRange(i + 1, 3).setValue(new Date().toISOString());
    sheet.getRange(i + 1, 4).setValue(true);
    return subscribeAck();
  }

  sheet.appendRow([email, generateToken(), new Date().toISOString(), true]);
  return subscribeAck();
}

function subscribeAck() {
  return HtmlService.createHtmlOutput('<!DOCTYPE html><html><body>ok</body></html>');
}

function handleUnsubscribe(token) {
  var result = unsubscribeToken(token);
  if (result.ok) {
    return HtmlService.createHtmlOutput(
      wrapPage(
        'Unsubscribed',
        '<p>You have been unsubscribed. You will not receive further emails.</p>' +
          '<p><a href="' + escapeHtml(getConfig().siteUrl) + '">Back to the blog</a></p>'
      )
    );
  }
  return HtmlService.createHtmlOutput(
    wrapPage('Unsubscribe', '<p>This unsubscribe link is invalid or has already been used.</p>')
  );
}

function handleUnsubscribePost(token) {
  var result = unsubscribeToken(token);
  return jsonResponse({ ok: result.ok });
}

function unsubscribeToken(token) {
  if (!token) {
    return { ok: false };
  }
  var sheet = getSheet();
  var data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][1] === token && isActive(data[i][3])) {
      sheet.getRange(i + 1, 4).setValue(false);
      return { ok: true };
    }
  }
  return { ok: false };
}

function getActiveSubscribers() {
  var sheet = getSheet();
  var data = sheet.getDataRange().getValues();
  var subscribers = [];
  for (var i = 1; i < data.length; i++) {
    if (!isActive(data[i][3])) {
      continue;
    }
    var email = normalizeEmail(data[i][0]);
    var token = data[i][1];
    if (email && token) {
      subscribers.push({ email: email, token: token });
    }
  }
  return subscribers;
}

function fetchTemplate(templateUrl) {
  if (!templateUrl) {
    throw new Error('TEMPLATE_URL script property is not set.');
  }
  var response = UrlFetchApp.fetch(templateUrl, { muteHttpExceptions: true });
  if (response.getResponseCode() !== 200) {
    throw new Error('Failed to fetch email template: HTTP ' + response.getResponseCode());
  }
  return response.getContentText();
}

function unsubscribePageUrl(token, cfg) {
  return cfg.siteUrl + '/unsubscribe/?t=' + encodeURIComponent(token);
}

function unsubscribeApiUrl(token, cfg) {
  return cfg.webAppUrl + '?action=unsubscribe&token=' + encodeURIComponent(token);
}

function renderTemplate(template, post, subscriber, cfg) {
  var unsubUrl = unsubscribePageUrl(subscriber.token, cfg);
  return template
    .replace(/\{\{SITE_TITLE\}\}/g, escapeHtml(cfg.siteTitle))
    .replace(/\{\{SITE_URL\}\}/g, escapeHtml(cfg.siteUrl))
    .replace(/\{\{POST_TITLE\}\}/g, escapeHtml(post.title || ''))
    .replace(/\{\{POST_DATE\}\}/g, escapeHtml(post.date || ''))
    .replace(/\{\{POST_URL\}\}/g, escapeHtml(post.url || ''))
    .replace(/\{\{POST_EXCERPT\}\}/g, escapeHtml(post.excerpt || ''))
    .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, escapeHtml(unsubUrl));
}

function plainTextFallback(post) {
  return (
    'New post: ' +
    (post.title || '') +
    '\n\n' +
    (post.excerpt || '') +
    '\n\nRead: ' +
    (post.url || '')
  );
}

function handleSend(payload) {
  var cfg = getConfig();
  if (!cfg.webhookSecret || payload.secret !== cfg.webhookSecret) {
    return jsonResponse({ ok: false, error: 'unauthorized' });
  }

  var post = payload.post || {};
  if (!post.title || !post.url) {
    return jsonResponse({ ok: false, error: 'missing post.title or post.url' });
  }

  var template = fetchTemplate(cfg.templateUrl);
  var subscribers = getActiveSubscribers();
  var sent = 0;

  for (var i = 0; i < subscribers.length; i++) {
    var sub = subscribers[i];
    var html = renderTemplate(template, post, sub, cfg);
    var oneClickUnsubUrl = unsubscribeApiUrl(sub.token, cfg);
    GmailApp.sendEmail(sub.email, 'New post: ' + post.title, plainTextFallback(post), {
      htmlBody: html,
      name: cfg.fromName,
      headers: {
        'List-Unsubscribe': '<' + oneClickUnsubUrl + '>',
        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
      },
    });
    sent++;
  }

  return jsonResponse({ ok: true, sent: sent });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function wrapPage(title, bodyHtml) {
  var cfg = getConfig();
  return (
    '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">' +
    '<title>' +
    escapeHtml(title) +
    '</title></head>' +
    '<body style="margin:0;padding:24px 12px;background:#3a6ea4;font-family:Tahoma,Verdana,sans-serif;">' +
    '<div style="max-width:520px;margin:0 auto;border:2px solid #0054e3;background:#ece9d8;">' +
    '<div style="padding:6px 10px;background:linear-gradient(#3c81f3,#0a42c7);color:#fff;font-weight:bold;font-size:13px;">' +
    escapeHtml(cfg.siteTitle) +
    '</div>' +
    '<div style="padding:16px 18px;font-size:13px;line-height:1.45;color:#000;">' +
    '<h1 style="margin:0 0 12px;font-size:18px;">' +
    escapeHtml(title) +
    '</h1>' +
    bodyHtml +
    '</div></div></body></html>'
  );
}

/** Run once from the editor to create the subscribers sheet header row. */
function setupSheet() {
  getSheet();
  Logger.log('Subscribers sheet is ready.');
}
