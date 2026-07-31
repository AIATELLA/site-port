# Form handler

Cloudflare Worker behind the waitlist and contact forms. It validates the
submission, stores a copy, emails the team, and sends the visitor to the
thank-you page.

Nothing here runs at build time — the static site is deployed exactly as it
is, and this Worker is deployed separately.

## What talks to what

```
waitlist.html  ──POST /api/waitlist──▶  Worker  ──▶ KV (durable copy)
contact.html   ──POST /api/contact───▶            └▶ Resend (email to the team)
                                          │
                                          └─── 303 or JSON ──▶ *-thanks page
```

`assets/js/forms.js` submits in place and shows errors inline. It is a
progressive enhancement: the forms carry a real `method`/`action`, so with
JavaScript unavailable the browser posts natively and the Worker's 303 does
the rest. Both paths are covered by tests.

## Deploying

```sh
cd workers/form-handler
npm install
npx wrangler login
```

**1. Sending address.** Add `aiatella.com` as a domain in Resend and
complete its DNS records, then create an API key:

```sh
npx wrangler secret put RESEND_API_KEY
```

Resend's free tier is 3,000 emails/month and 100/day, which is far above
what these two forms will produce. MailChannels, which older Cloudflare
guides recommend, is no longer free for Workers.

**2. Durable copy of every submission** (optional, strongly recommended).
Without it a Resend outage means a lost enquiry; with it the submission is
written to KV first and only then emailed. It also backs the per-IP rate
limiter.

```sh
npx wrangler kv namespace create SUBMISSIONS
```

Paste the printed id into `wrangler.toml` and uncomment that block.

**3. Route.** Preferred: put the Worker on the site's own hostname, so the
forms post to a relative path and there is no CORS to keep in sync.
Uncomment the `[[routes]]` block in `wrangler.toml`:

```toml
[[routes]]
pattern = "www.aiatella.com/api/*"
zone_name = "aiatella.com"
```

If the site is not served from this Cloudflare zone, deploy to
`forms.aiatella.com` instead and change the two form `action` attributes to
the absolute URL. `ALLOWED_ORIGINS` already lists the site origins, which
is what makes the CORS preflight succeed.

**4. Deploy and watch.**

```sh
npx wrangler deploy
npx wrangler tail          # live logs, including any mail failures
```

## Checking it works

```sh
npm test                   # 25 tests, no network, no wrangler needed
npx wrangler dev           # local Worker on :8787
curl -i -X POST http://localhost:8787/api/contact \
  -H 'Accept: application/json' \
  -d 'Name=Test&Email=test@example.com&Message=Hello'
```

Expect `{"ok":true,"redirect":"/contact-thanks"}`. Without
`RESEND_API_KEY` set locally you will get a 502 `delivery_failed`, which is
the correct answer: nothing was stored and nothing was sent, so the
visitor must not be told it worked.

## Settings

Set in `wrangler.toml` under `[vars]`, except secrets.

| Name | Purpose |
| --- | --- |
| `MAIL_TO` | Recipients, comma-separated. |
| `MAIL_FROM` | Sender. Must be verified in Resend. |
| `ALLOWED_ORIGINS` | Origins allowed to post. A request from any other origin is refused. |
| `SPAM_MODE` | `flag` (default) or `drop`. See below. |
| `RESEND_API_KEY` | Secret. `wrangler secret put`. |
| `TURNSTILE_SECRET` | Secret, optional. Setting it turns on captcha checking. |

## Two decisions worth knowing about

**Honeypots flag, they do not drop.** Framer's export ships hidden fields
that bots fill in and humans do not. A tripped honeypot adds
`[possible spam]` to the subject and delivers anyway, rather than binning
the message. The reasoning: an aggressive password manager can fill a
hidden field for a real person, and silently destroying a clinical
partnership enquiry is far worse than an occasional flagged email in the
inbox. Switch `SPAM_MODE` to `drop` if flagged mail becomes a nuisance —
that answers a bot with an apparent success so it has nothing to tune
against.

**Field names are case-sensitive, and that is load-bearing.** The
honeypots are named `company` and `message`; the real fields are `Company`
and `Message`. They differ by capitalisation alone. Normalising field names
to lower case would make the honeypot check read the visitor's own message
and flag every genuine enquiry as spam. There are tests specifically
guarding this — if they ever start failing, that is why.

## Adding a field to a form

1. Add the input to `waitlist.html` or `contact.html`. Pick a name that
   does not collide case-insensitively with a honeypot (see `HONEYPOTS` in
   `src/index.js`).
2. Add it to the matching entry in `FORMS` in `src/index.js`, with a `max`
   length and `required: true` if it is mandatory.

Anything not listed in `FORMS` is ignored rather than forwarded, so a field
added to the page but not here will submit fine and quietly never arrive.

## Still outstanding

- The privacy policy names Resend and Cloudflare as processors. If the mail
  provider changes, that text needs changing too.
- Turnstile is wired up but off. Turn it on if spam gets past the honeypots:
  set `TURNSTILE_SECRET` and add the widget to both forms.
