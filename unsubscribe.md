---

layout: page
title: Unsubscribe
permalink: /unsubscribe/

---

{% assign newsletter_url = site.newsletter.apps_script_url %}

Unsubscribing…

**You have been unsubscribed**; you will not receive further emails. Sorry to see you go, but grateful for your support!

[Back to the blog]({{ '/' | relative_url }})

# Unsubscribe

Use the **Unsubscribe** link at the bottom of any newsletter email. It works in one click, no login required.

If the link does not work, reply to the newsletter email with the word `unsubscribe` and I will remove you manually.

[Back to the blog]({{ '/' | relative_url }})

{% unless newsletter_url == "" or newsletter_url contains "REPLACE_ME" %}



{% endunless %}