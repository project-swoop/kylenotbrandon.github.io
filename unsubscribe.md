---
layout: page
title: Unsubscribe
permalink: /unsubscribe/
---

{% assign newsletter_url = site.newsletter.apps_script_url %}

<div id="unsubscribe-working" class="newsletter-panel newsletter-is-hidden">
  <p>Unsubscribing…</p>
</div>

<div id="unsubscribe-success" class="newsletter-panel newsletter-success newsletter-is-hidden">
  <p><strong>You have been unsubscribed</strong>; you will not receive further emails. Sorry to see you go, but grateful for your support!</p>
  <p><a href="{{ '/' | relative_url }}">Back to the blog</a></p>
</div>

<div id="unsubscribe-help">
  <h1 class="page-title">Unsubscribe</h1>
  <p>Use the <strong>Unsubscribe</strong> link at the bottom of any newsletter email. It works in one click, no login required.</p>
  <p>If the link does not work, reply to the newsletter email with the word <code>unsubscribe</code> and I will remove you manually.</p>
  <p><a href="{{ '/' | relative_url }}">Back to the blog</a></p>
</div>

{% unless newsletter_url == "" or newsletter_url contains "REPLACE_ME" %}
<script>
(function () {
  var params = new URLSearchParams(window.location.search);
  var token = params.get('t');
  if (!token) return;

  var apiUrl = {{ newsletter_url | jsonify }};
  var working = document.getElementById('unsubscribe-working');
  var success = document.getElementById('unsubscribe-success');
  var help = document.getElementById('unsubscribe-help');

  function showNode(el) {
    if (el) el.classList.remove('newsletter-is-hidden');
  }

  function hideNode(el) {
    if (el) el.classList.add('newsletter-is-hidden');
  }

  showNode(working);
  hideNode(help);

  var request = fetch(
    apiUrl + '?action=unsubscribe&token=' + encodeURIComponent(token),
    { method: 'GET', mode: 'no-cors' }
  );

  Promise.resolve(request).finally(function () {
    hideNode(working);
    showNode(success);
  });
})();
</script>
<noscript>
  <p class="newsletter-notice">JavaScript is required to unsubscribe on this page. Use the unsubscribe link in your email client, or email me directly.</p>
</noscript>
{% endunless %}
