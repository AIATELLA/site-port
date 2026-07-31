/**
 * AIATELLA website form handler.
 *
 * Receives the waitlist and contact form POSTs, validates them, stores a
 * copy, emails the team, and sends the visitor to the thank-you page.
 *
 * Two deployment shapes are supported, and the code is the same for both:
 *
 *   1. Same origin (preferred). A Worker route on the site's own zone,
 *      e.g. `www.aiatella.com/api/*`. No CORS involved, so the forms can
 *      post to a relative path and there is nothing to keep in sync.
 *   2. Separate host. e.g. `forms.aiatella.com`, for when the site is not
 *      served from this Cloudflare zone. Set ALLOWED_ORIGINS and the CORS
 *      preflight below takes care of the rest.
 *
 * Design notes that are easy to get wrong later:
 *
 *   - Field names are CASE-SENSITIVE and that is load-bearing. Framer's
 *     export ships spam honeypots named `company` and `message`, which
 *     collide case-insensitively with the real `Company` and `Message`
 *     fields. FormData.get() is case-sensitive so this works, but do not
 *     "tidy" it by lowercasing keys -- that would read a honeypot as the
 *     visitor's message and silently bin every real enquiry.
 *   - A tripped honeypot FLAGS by default, it does not drop. Every
 *     enquiry here is potentially a clinical partnership; an aggressive
 *     password manager filling a hidden field must not silently destroy
 *     one. Set SPAM_MODE = "drop" if the flagged mail becomes a nuisance.
 *   - Mail is sent AFTER the submission is persisted, so a provider
 *     outage costs a notification, never the lead itself.
 */

const FORMS = {
  waitlist: {
    label: "Waitlist",
    next: "waitlist-thanks",
    fields: [
      { name: "Name", required: true, max: 200 },
      { name: "Email", required: true, max: 320, kind: "email" },
      { name: "Region", required: true, max: 200, label: "City/Region" },
      { name: "Phone Number", max: 60 },
      { name: "Organization", max: 200 },
      { name: "Message", max: 5000 },
      { name: "Radio", max: 20, label: "Preferred location",
        oneOf: ["Clinic", "Event", "Workplace", "Any"] },
    ],
  },
  contact: {
    label: "Contact",
    next: "contact-thanks",
    fields: [
      { name: "Name", required: true, max: 200 },
      { name: "Email", required: true, max: 320, kind: "email" },
      { name: "Phone Number", max: 60 },
      { name: "Company", max: 200 },
      { name: "Role", max: 200 },
      { name: "Message", required: true, max: 5000 },
    ],
  },
};

/** Hidden inputs Framer ships to catch bots. Lowercase, unlike real fields. */
const HONEYPOTS = ["website", "company", "message", "subject", "title",
  "description", "feedback", "notes", "details", "remarks", "comments"];

/** Redirect targets a form is allowed to ask for. Guards against an open redirect. */
const THANKS = new Set([
  "waitlist-thanks", "waitlist-thanks.html",
  "contact-thanks", "contact-thanks.html",
]);

const MAX_BODY = 64 * 1024;
const RATE_WINDOW = 60;   // seconds
const RATE_MAX = 5;       // submissions per IP per window

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const slug = url.pathname.replace(/^\/+|\/+$/g, "").split("/").pop();
    const form = FORMS[slug];

    if (request.method === "OPTIONS") return preflight(request, env);
    if (!form) return json({ error: "not_found" }, 404, request, env);
    if (request.method !== "POST") {
      return json({ error: "method_not_allowed" }, 405, request, env,
        { Allow: "POST, OPTIONS" });
    }

    // Reject cross-site posts when we know which origins are ours. A missing
    // Origin header is allowed through: non-browser clients omit it, and the
    // honeypot plus validation already cover the cheap-bot case.
    const origin = request.headers.get("Origin");
    const allowed = originAllowlist(env);
    if (origin && allowed.length && !allowed.includes(origin)) {
      return json({ error: "forbidden_origin" }, 403, request, env);
    }

    const declared = Number(request.headers.get("Content-Length") || 0);
    if (declared > MAX_BODY) {
      return json({ error: "too_large" }, 413, request, env);
    }

    let body;
    try {
      body = await readBody(request);
    } catch (err) {
      return json({ error: "bad_request", detail: String(err.message) }, 400, request, env);
    }

    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    if (await rateLimited(env, ip)) {
      return json({ error: "rate_limited" }, 429, request, env,
        { "Retry-After": String(RATE_WINDOW) });
    }

    if (env.TURNSTILE_SECRET) {
      const ok = await verifyTurnstile(env.TURNSTILE_SECRET, body.get("cf-turnstile-response"), ip);
      if (!ok) return json({ error: "captcha_failed" }, 400, request, env);
    }

    const { values, errors } = validate(form, body);
    if (errors.length) {
      return json({ error: "validation_failed", fields: errors }, 422, request, env);
    }

    const tripped = HONEYPOTS.filter((n) => (body.get(n) || "").trim() !== "");
    if (tripped.length && (env.SPAM_MODE || "flag") === "drop") {
      // Answer as if it worked so a bot has nothing to tune against.
      return finish(request, env, form, body, { dropped: true });
    }

    const submission = {
      form: slug,
      receivedAt: new Date().toISOString(),
      values,
      suspectedSpam: tripped.length > 0,
      honeypotsTripped: tripped,
      meta: {
        ip,
        country: request.cf && request.cf.country,
        userAgent: request.headers.get("User-Agent") || "",
        referer: request.headers.get("Referer") || "",
      },
    };

    const stored = await store(env, submission);
    const mailed = await sendMail(env, form, submission);

    if (!stored && !mailed.ok) {
      // Nothing durable happened, so do not tell the visitor it worked.
      console.error("submission lost", slug, mailed.error);
      return json({ error: "delivery_failed" }, 502, request, env);
    }
    if (!mailed.ok) console.error("mail failed but submission stored", mailed.error);

    return finish(request, env, form, body, {});
  },
};

/* ---------------------------------------------------------------- parsing */

async function readBody(request) {
  const type = (request.headers.get("Content-Type") || "").split(";")[0].trim();
  if (type === "application/json") {
    const raw = await request.text();
    if (raw.length > MAX_BODY) throw new Error("body too large");
    const obj = JSON.parse(raw);
    if (!obj || typeof obj !== "object") throw new Error("expected a JSON object");
    const fd = new FormData();
    for (const [k, v] of Object.entries(obj)) {
      if (v !== null && v !== undefined) fd.set(k, String(v));
    }
    return fd;
  }
  // Covers both application/x-www-form-urlencoded (native form POST) and
  // multipart/form-data.
  return await request.formData();
}

function validate(form, body) {
  const values = {};
  const errors = [];
  for (const f of form.fields) {
    const raw = body.get(f.name);
    const value = typeof raw === "string" ? raw.trim() : "";
    if (!value) {
      if (f.required) errors.push({ field: f.name, error: "required" });
      continue;
    }
    if (value.length > f.max) {
      errors.push({ field: f.name, error: "too_long", max: f.max });
      continue;
    }
    if (f.kind === "email" && !looksLikeEmail(value)) {
      errors.push({ field: f.name, error: "invalid_email" });
      continue;
    }
    if (f.oneOf && !f.oneOf.includes(value)) {
      errors.push({ field: f.name, error: "not_allowed" });
      continue;
    }
    values[f.name] = value;
  }
  return { values, errors };
}

/**
 * Deliberately permissive. The only thing worth rejecting here is input
 * that cannot be an address at all; anything stricter starts refusing
 * valid addresses, and the real proof is whether a reply arrives.
 */
function looksLikeEmail(v) {
  return /^[^\s@,;]+@[^\s@,;.]+(\.[^\s@,;.]+)+$/.test(v) && v.length <= 320;
}

/* --------------------------------------------------------------- storage */

async function store(env, submission) {
  if (!env.SUBMISSIONS) return false;
  try {
    const key = `sub:${submission.receivedAt}:${submission.form}:${crypto.randomUUID().slice(0, 8)}`;
    await env.SUBMISSIONS.put(key, JSON.stringify(submission, null, 2));
    return true;
  } catch (err) {
    console.error("KV put failed", err);
    return false;
  }
}

/**
 * Fixed-window counter. Coarse, and two racing requests can both read the
 * same count -- acceptable, because the job here is stopping a script from
 * emptying the mail quota, not exact accounting.
 */
async function rateLimited(env, ip) {
  if (!env.SUBMISSIONS || ip === "unknown") return false;
  const bucket = Math.floor(Date.now() / 1000 / RATE_WINDOW);
  const key = `rl:${bucket}:${ip}`;
  try {
    const n = Number((await env.SUBMISSIONS.get(key)) || 0);
    if (n >= RATE_MAX) return true;
    await env.SUBMISSIONS.put(key, String(n + 1), { expirationTtl: RATE_WINDOW * 2 });
    return false;
  } catch (err) {
    console.error("rate limit check failed, allowing", err);
    return false;
  }
}

/* ------------------------------------------------------------------ mail */

async function sendMail(env, form, submission) {
  if (!env.RESEND_API_KEY) return { ok: false, error: "RESEND_API_KEY not configured" };

  const v = submission.values;
  const who = v.Name || v.Email || "someone";
  const where = form.label === "Waitlist"
    ? (v.Region ? ` (${v.Region})` : "")
    : (v.Company ? ` (${v.Company})` : "");
  const flag = submission.suspectedSpam ? "[possible spam] " : "";
  const subject = `${flag}AIATELLA ${form.label.toLowerCase()} — ${who}${where}`;

  const lines = [];
  for (const f of form.fields) {
    if (v[f.name] === undefined) continue;
    lines.push(`${f.label || f.name}: ${v[f.name]}`);
  }
  lines.push("", "—".repeat(40));
  lines.push(`Form: ${submission.form}`);
  lines.push(`Received: ${submission.receivedAt}`);
  if (submission.meta.country) lines.push(`Country: ${submission.meta.country}`);
  lines.push(`IP: ${submission.meta.ip}`);
  if (submission.meta.referer) lines.push(`Page: ${submission.meta.referer}`);
  if (submission.suspectedSpam) {
    lines.push("", `Honeypot fields were filled in: ${submission.honeypotsTripped.join(", ")}.`);
    lines.push("Probably a bot, but delivered anyway so a real enquiry is never lost.");
  }

  const payload = {
    from: env.MAIL_FROM || "AIATELLA website <forms@aiatella.com>",
    to: (env.MAIL_TO || "onni@aiatella.com").split(",").map((s) => s.trim()),
    subject,
    text: lines.join("\n"),
  };
  if (v.Email) payload.reply_to = v.Email;

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return { ok: false, error: `${res.status} ${await res.text()}` };
    return { ok: true };
  } catch (err) {
    return { ok: false, error: String(err) };
  }
}

/* --------------------------------------------------------------- captcha */

async function verifyTurnstile(secret, token, ip) {
  if (!token) return false;
  const fd = new FormData();
  fd.set("secret", secret);
  fd.set("response", String(token));
  if (ip && ip !== "unknown") fd.set("remoteip", ip);
  try {
    const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify",
      { method: "POST", body: fd });
    const out = await res.json();
    return out.success === true;
  } catch (err) {
    console.error("turnstile verify failed", err);
    return false;
  }
}

/* -------------------------------------------------------------- response */

/**
 * A fetch caller (Accept: application/json) gets JSON and navigates
 * itself; a plain form POST with JavaScript unavailable gets a 303 so the
 * thank-you page lands under a GET and survives a refresh.
 */
function finish(request, env, form, body, opts) {
  const asked = String(body.get("_next") || "");
  const target = "/" + (THANKS.has(asked) ? asked : form.next);
  const wantsJson = (request.headers.get("Accept") || "").includes("application/json");
  if (wantsJson) {
    return json({ ok: true, redirect: target, dropped: !!opts.dropped }, 200, request, env);
  }
  return new Response(null, {
    status: 303,
    headers: { Location: target, ...corsHeaders(request, env) },
  });
}

function json(obj, status, request, env, extra) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...corsHeaders(request, env),
      ...(extra || {}),
    },
  });
}

function originAllowlist(env) {
  return String(env.ALLOWED_ORIGINS || "")
    .split(",").map((s) => s.trim()).filter(Boolean);
}

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin");
  const allowed = originAllowlist(env);
  if (!origin || !allowed.includes(origin)) return {};
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Credentials": "false",
    Vary: "Origin",
  };
}

function preflight(request, env) {
  const headers = corsHeaders(request, env);
  if (!headers["Access-Control-Allow-Origin"]) return new Response(null, { status: 403 });
  return new Response(null, {
    status: 204,
    headers: {
      ...headers,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Accept",
      "Access-Control-Max-Age": "86400",
    },
  });
}
