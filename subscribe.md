---
layout: page
title: Subscribe
permalink: /subscribe/
---

# Subscribe by email

Get an email every time I publish a new post. Nothing needed but your email. And certainly no pressure to unsubscribe at any moment.

{% assign newsletter_url = site.newsletter.apps_script_url %}
{% if newsletter_url == "" or newsletter_url contains "REPLACE_ME" %}
<p class="newsletter-notice"><strong>Newsletter signup is not configured yet.</strong> See <code>docs/newsletter-setup.md</code> in the repo.</p>
{% else %}
<div id="newsletter-success" class="newsletter-panel newsletter-success" hidden>
  <p><strong>You are subscribed!</strong> You will get an email when any future posts go live. Thank you so much for supporting the blog! (As a fair warning, any emails <em>could</em> end up in your spam/junk folder.)</p>
</div>

<div id="newsletter-error" class="newsletter-panel newsletter-error" hidden>
  <p><strong>Something went wrong.</strong> Please try again in a moment.</p>
</div>

<form id="newsletter-form" class="newsletter-form" action="{{ newsletter_url }}" method="post" target="newsletter-frame" data-api-url="{{ newsletter_url }}">
  <input type="hidden" name="action" value="subscribe">
  <div class="newsletter-field">
    <label for="newsletter-email">Email address</label>
    <input id="newsletter-email" name="email" type="email" required autocomplete="email" placeholder="you@example.com">
  </div>
  <button id="newsletter-submit" type="submit" class="newsletter-button">Subscribe</button>
</form>

<iframe id="newsletter-frame" class="newsletter-hidden-frame" name="newsletter-frame" title="Newsletter signup" tabindex="-1"></iframe>

<p class="newsletter-fine-print">One email per new post. Unsubscribe at any time through the link at the bottom of each email.</p>

<script>
(function () {
  var form = document.getElementById('newsletter-form');
  var frame = document.getElementById('newsletter-frame');
  var submitBtn = document.getElementById('newsletter-submit');
  var success = document.getElementById('newsletter-success');
  var error = document.getElementById('newsletter-error');
  if (!form || !frame) return;

  function showSuccess() {
    if (success) success.hidden = false;
    if (error) error.hidden = true;
    form.hidden = true;
  }

  function showError() {
    if (error) error.hidden = false;
    if (submitBtn) submitBtn.disabled = false;
  }

  form.addEventListener('submit', function () {
    if (submitBtn) submitBtn.disabled = true;
    if (error) error.hidden = true;

    var timedOut = false;
    var timeout = window.setTimeout(function () {
      timedOut = true;
      showError();
    }, 15000);

    frame.onload = function () {
      window.clearTimeout(timeout);
      if (!timedOut) showSuccess();
      frame.onload = null;
    };
  });
})();
</script>
{% endif %}
