---

layout: page
title: Subscribe
permalink: /subscribe/

---

# Subscribe by email

Get an email every time I publish a new post. Nothing needed but your email. And certainly no pressure to unsubscribe at any moment.

{% assign newsletter_url = site.newsletter.apps_script_url %}
{% if newsletter_url == "" or newsletter_url contains "REPLACE_ME" %}

**Newsletter signup is not configured yet.** See `docs/newsletter-setup.md` in the repo.

 {% else %}

**You are subscribed!** You will get an email when any future posts go live. Thank you so much for supporting the blog! (As a fair warning, any emails *could* end up in your spam/junk folder.)

**Something went wrong.** Please try again in a moment.

Email address

Subscribe

One email per new post. Unsubscribe at any time through the link at the bottom of each email.

{% endif %}