---
layout: page
title: Subscribe
permalink: /subscribe/

---

# Subscribe by email

Get an email when I publish a new post. No account needed — just your address.

{% assign newsletter_url = site.newsletter.apps_script_url %}
{% if newsletter_url == "" or newsletter_url contains "REPLACE_ME" %}
<p class="newsletter-notice"><strong>Newsletter signup is not configured yet.</strong> See <code>docs/newsletter-setup.md</code> in the repo.</p>
{% else %}
<div id="newsletter-success" class="newsletter-panel newsletter-success" hidden>
  <p><strong>You are subscribed.</strong> You will get an email when the next post goes live.</p>
</div>

<form class="newsletter-form" action="{{ newsletter_url }}" method="post">
  <input type="hidden" name="action" value="subscribe">
  <div class="newsletter-field">
    <label for="newsletter-email">Email address</label>
    <input id="newsletter-email" name="email" type="email" required autocomplete="email" placeholder="you@example.com">
  </div>
  <button type="submit" class="newsletter-button">Subscribe</button>
</form>

<p class="newsletter-fine-print">One email per new post. Every message includes a one-click unsubscribe link.</p>

<script>
(function () {
  var params = new URLSearchParams(window.location.search);
  if (params.get('done') !== '1') return;
  var panel = document.getElementById('newsletter-success');
  var form = document.querySelector('.newsletter-form');
  if (panel) panel.hidden = false;
  if (form) form.hidden = true;
})();
</script>
{% endif %}
