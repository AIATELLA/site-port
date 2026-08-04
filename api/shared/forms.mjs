/**
 * Shared form handling: validation, spam detection, email, storage.
 * Ported from Cloudflare Worker (workers/form-handler/src/index.js).
 */

// --- Form definitions ---

const FORMS = {
  waitlist: {
    fields: [
      { name: "Name", required: true, max: 120, kind: "text" },
      { name: "Email", required: true, max: 254, kind: "email" },
      { name: "Region", required: true, max: 120, kind: "text" },
      { name: "Phone Number", max: 40, kind: "text" },
      { name: "Organization", max: 200, kind: "text" },
      { name: "Radio", max: 60, kind: "text", oneOf: ["Clinic", "Event", "Workplace", "Any"] },
      { name: "Message", max: 2000, kind: "text" },
    ],
    subject: "New Waitlist Signup",
  },
  contact: {
    fields: [
      { name: "Name", required: true, max: 120, kind: "text" },
      { name: "Email", required: true, max: 254, kind: "email" },
      { name: "Phone Number", max: 40, kind: "text" },
      { name: "Company", max: 200, kind: "text" },
      { name: "Role", max: 120, kind: "text" },
      { name: "Message", required: true, max: 5000, kind: "text" },
    ],
    subject: "New Contact Form Submission",
  },
};

// Honeypot field names (lowercase versions of real fields)
const HONEYPOTS = new Set([
  "website", "company", "message", "subject", "title",
  "description", "feedback", "notes", "details", "remarks", "comments",
]);

const REDIRECT_ALLOW = new Set([
  "waitlist-thanks", "waitlist-thanks.html",
  "contact-thanks", "contact-thanks.html",
]);

const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 5;

// --- Validation ---

function validateForm(formName, body) {
  const spec = FORMS[formName];
  if (!spec) return { ok: false, status: 400, error: `Unknown form: ${formName}` };

  // Honeypot check
  for (const key of Object.keys(body)) {
    if (HONEYPOTS.has(key)) {
      // Silent accept — pretend success to bots
      return { ok: false, status: 200, silent: true };
    }
  }

  const errors = {};
  const cleaned = {};

  for (const field of spec.fields) {
    let val = (body[field.name] ?? "").toString().trim();
    if (field.required && !val) {
      errors[field.name] = `${field.name} is required`;
      continue;
    }
    if (!val) continue;
    if (val.length > field.max) {
      errors[field.name] = `${field.name} must be under ${field.max} characters`;
      continue;
    }
    if (field.kind === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
      errors[field.name] = "Invalid email address";
      continue;
    }
    if (field.oneOf && !field.oneOf.includes(val)) {
      errors[field.name] = `Must be one of: ${field.oneOf.join(", ")}`;
      continue;
    }
    cleaned[field.name] = val;
  }

  if (Object.keys(errors).length) {
    return { ok: false, status: 422, errors };
  }

  return { ok: true, cleaned, subject: spec.subject };
}

// --- Turnstile ---

async function verifyTurnstile(token, ip, secret) {
  if (!secret || !token) return true; // skip if not configured
  const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ secret, response: token, remoteip: ip }),
  });
  const data = await res.json();
  return data.success === true;
}

// --- Rate limiting (Azure Table Storage) ---

async function checkRateLimit(tableClient, ip) {
  if (!tableClient) return { allowed: true };

  const now = Date.now();
  const windowStart = now - RATE_WINDOW_MS;
  const partitionKey = "ratelimit";
  const rowKey = ip.replace(/[:/]/g, "_");

  try {
    const entity = await tableClient.getEntity(partitionKey, rowKey);
    const windowTs = entity.windowStart ?? 0;
    const count = entity.count ?? 0;

    if (windowTs > windowStart && count >= RATE_MAX) {
      return { allowed: false, retryAfter: Math.ceil((windowTs + RATE_WINDOW_MS - now) / 1000) };
    }

    const newCount = windowTs > windowStart ? count + 1 : 1;
    const newWindowStart = windowTs > windowStart ? windowTs : now;

    await tableClient.upsertEntity({
      partitionKey, rowKey,
      windowStart: newWindowStart,
      count: newCount,
    });

    return { allowed: true };
  } catch (e) {
    if (e.statusCode === 404) {
      await tableClient.upsertEntity({
        partitionKey, rowKey,
        windowStart: now,
        count: 1,
      });
      return { allowed: true };
    }
    // If storage fails, allow the request (fail open)
    console.error("Rate limit check failed:", e.message);
    return { allowed: true };
  }
}

// --- Store submission ---

async function storeSubmission(tableClient, formName, cleaned, ip) {
  if (!tableClient) return;

  try {
    await tableClient.createEntity({
      partitionKey: formName,
      rowKey: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      ip,
      ...cleaned,
      submittedAt: new Date().toISOString(),
    });
  } catch (e) {
    console.error("Failed to store submission:", e.message);
    // Non-fatal — email is the primary delivery
  }
}

// --- Send email via Azure Communication Services ---

async function sendEmail(connectionString, mailTo, mailFrom, subject, formName, cleaned) {
  const { EmailClient } = await import("@azure/communication-email");
  const client = new EmailClient(connectionString);

  const lines = Object.entries(cleaned)
    .map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;font-weight:600">${k}</td><td style="padding:4px 0">${v}</td></tr>`)
    .join("\n");

  const html = `
    <h2>${subject}</h2>
    <table style="border-collapse:collapse">${lines}</table>
    <p style="margin-top:24px;color:#888;font-size:12px">
      Submitted via aiatella.com/${formName} form
    </p>`;

  const poller = await client.beginSend({
    senderAddress: mailFrom,
    content: {
      subject: `${subject} — ${cleaned.Name ?? "Unknown"}`,
      html,
    },
    recipients: {
      to: mailTo.split(",").map(a => ({ address: a.trim() })),
    },
    ...(cleaned.Email ? { replyTo: [{ address: cleaned.Email }] } : {}),
  });

  const result = await poller.pollUntilDone();
  if (result.status !== "Succeeded") {
    throw new Error(`ACS Email error: ${result.status} — ${JSON.stringify(result.error)}`);
  }
}


// --- Main handler ---

export async function handleFormSubmission(request, formName, { tableClient } = {}) {
  const ACS_EMAIL_CONNECTION_STRING = process.env.ACS_EMAIL_CONNECTION_STRING;
  const TURNSTILE_SECRET = process.env.TURNSTILE_SECRET;
  const MAIL_TO = process.env.MAIL_TO || "contact@aiatella.com,onni@aiatella.com";
  const MAIL_FROM = process.env.MAIL_FROM || "forms@aiatella.com";
  const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "https://www.aiatella.com,https://aiatella.com").split(",");

  const origin = request.headers.get("origin");
  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  const wantsJson = (request.headers.get("accept") || "").includes("application/json");

  // CORS preflight
  if (request.method === "OPTIONS") {
    const corsHeaders = {};
    if (origin && ALLOWED_ORIGINS.includes(origin)) {
      corsHeaders["Access-Control-Allow-Origin"] = origin;
      corsHeaders["Access-Control-Allow-Methods"] = "POST, OPTIONS";
      corsHeaders["Access-Control-Allow-Headers"] = "Content-Type, Accept";
      corsHeaders["Access-Control-Max-Age"] = "86400";
    }
    return { status: 204, headers: corsHeaders, body: null };
  }

  if (request.method !== "POST") {
    return { status: 405, body: { error: "Method not allowed" } };
  }

  // Parse body
  const contentType = request.headers.get("content-type") || "";
  let body;
  if (contentType.includes("application/json")) {
    body = await request.json();
  } else {
    const formData = await request.formData();
    body = Object.fromEntries(formData.entries());
  }

  // Rate limit
  const rl = await checkRateLimit(tableClient, ip);
  if (!rl.allowed) {
    const resp = { status: 429, body: { error: "Too many submissions. Try again shortly." } };
    if (rl.retryAfter) resp.headers = { "Retry-After": String(rl.retryAfter) };
    return resp;
  }

  // Turnstile
  const turnstileToken = body["cf-turnstile-response"];
  if (TURNSTILE_SECRET) {
    const ok = await verifyTurnstile(turnstileToken, ip, TURNSTILE_SECRET);
    if (!ok) {
      return { status: 403, body: { error: "Captcha verification failed" } };
    }
  }
  delete body["cf-turnstile-response"];

  // Extract _next before validation
  const nextPage = body._next;
  delete body._next;

  // Validate
  const result = validateForm(formName, body);
  if (!result.ok) {
    if (result.silent) {
      // Honeypot triggered — fake success
      if (wantsJson) return { status: 200, body: { ok: true } };
      const redirect = nextPage && REDIRECT_ALLOW.has(nextPage) ? `/${nextPage.replace(/\.html$/, "")}` : "/";
      return { status: 303, headers: { Location: redirect }, body: null };
    }
    return { status: result.status, body: result.errors ? { errors: result.errors } : { error: result.error } };
  }

  // Store
  await storeSubmission(tableClient, formName, result.cleaned, ip);

  // Email
  if (!ACS_EMAIL_CONNECTION_STRING) {
    console.error("ACS_EMAIL_CONNECTION_STRING not set — skipping email");
  } else {
    await sendEmail(ACS_EMAIL_CONNECTION_STRING, MAIL_TO, MAIL_FROM, result.subject, formName, result.cleaned);
  }

  // Success response
  const corsHeaders = {};
  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    corsHeaders["Access-Control-Allow-Origin"] = origin;
  }

  if (wantsJson) {
    return { status: 200, body: { ok: true }, headers: corsHeaders };
  }

  const redirect = nextPage && REDIRECT_ALLOW.has(nextPage) ? `/${nextPage.replace(/\.html$/, "")}` : "/";
  return { status: 303, headers: { ...corsHeaders, Location: redirect }, body: null };
}
