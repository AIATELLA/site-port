/**
 * Tests for the form handler, run on plain Node: the Worker only uses web
 * platform APIs, so `node --test test/` exercises the real module with no
 * wrangler, no container and no network.
 *
 * The case-sensitivity tests are the important ones. Framer's honeypots are
 * named `company` and `message`, which differ from the real `Company` and
 * `Message` fields by capitalisation alone. If anyone ever normalises field
 * names, the honeypot check starts reading the visitor's own message and
 * every genuine enquiry gets flagged as spam -- these tests are what will
 * catch that.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

/* -------------------------------------------------------------- harness */

function kv() {
  const map = new Map();
  return {
    map,
    async get(k) { return map.has(k) ? map.get(k) : null; },
    async put(k, v) { map.set(k, v); },
  };
}

function makeEnv(over = {}) {
  return {
    RESEND_API_KEY: "re_test_key",
    MAIL_TO: "onni@aiatella.com",
    MAIL_FROM: "AIATELLA website <forms@aiatella.com>",
    ALLOWED_ORIGINS: "https://www.aiatella.com",
    SUBMISSIONS: kv(),
    ...over,
  };
}

/** Swap in a fake global fetch so nothing leaves the machine; returns the calls. */
function captureMail(fn) {
  const real = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init, body: JSON.parse(init.body) });
    return new Response(JSON.stringify({ id: "test" }), { status: 200 });
  };
  return Promise.resolve(fn(calls)).finally(() => { globalThis.fetch = real; });
}

function post(path, fields, { headers = {}, env } = {}) {
  const body = new URLSearchParams();
  for (const [k, v] of Object.entries(fields)) body.append(k, v);
  const request = new Request(`https://www.aiatella.com${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Origin: "https://www.aiatella.com",
      ...headers,
    },
    body,
  });
  return worker.fetch(request, env || makeEnv(), {});
}

const VALID_WAITLIST = {
  Name: "Aino Virtanen",
  Email: "aino@example.fi",
  Region: "Helsinki",
  "Phone Number": "+358 40 1234567",
  Organization: "Terveystalo",
  Message: "Interested in a workplace screening day.",
  Radio: "Workplace",
  _next: "waitlist-thanks.html",
};

const VALID_CONTACT = {
  Name: "Onni Eriksson",
  Email: "onni@example.com",
  Message: "Please get in touch about a clinical pilot.",
  Company: "Example Health",
  Role: "CTO",
};

/* ------------------------------------------------------------ happy path */

test("a valid waitlist post redirects to the thank-you page", async () => {
  await captureMail(async () => {
    const res = await post("/api/waitlist", VALID_WAITLIST);
    assert.equal(res.status, 303);
    assert.equal(res.headers.get("Location"), "/waitlist-thanks.html");
  });
});

test("a fetch caller gets JSON with the redirect target instead of a 303", async () => {
  await captureMail(async () => {
    const res = await post("/api/contact", VALID_CONTACT,
      { headers: { Accept: "application/json" } });
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.ok, true);
    assert.equal(body.redirect, "/contact-thanks");
  });
});

test("every submitted field reaches the email, and reply-to is the visitor", async () => {
  await captureMail(async (calls) => {
    await post("/api/waitlist", VALID_WAITLIST);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "https://api.resend.com/emails");
    const mail = calls[0].body;
    assert.equal(mail.reply_to, "aino@example.fi");
    assert.deepEqual(mail.to, ["onni@aiatella.com"]);
    assert.match(mail.subject, /^AIATELLA waitlist — Aino Virtanen \(Helsinki\)$/);
    for (const v of ["Aino Virtanen", "aino@example.fi", "Helsinki",
      "+358 40 1234567", "Terveystalo", "workplace screening day", "Workplace"]) {
      assert.ok(mail.text.includes(v), `email is missing ${v}`);
    }
  });
});

test("the submission is persisted before the mail goes out", async () => {
  const env = makeEnv();
  await captureMail(async () => {
    await post("/api/contact", VALID_CONTACT, { env });
  });
  const keys = [...env.SUBMISSIONS.map.keys()].filter((k) => k.startsWith("sub:"));
  assert.equal(keys.length, 1);
  const saved = JSON.parse(env.SUBMISSIONS.map.get(keys[0]));
  assert.equal(saved.form, "contact");
  assert.equal(saved.values.Company, "Example Health");
  assert.equal(saved.suspectedSpam, false);
});

test("multipart bodies are handled -- this is what browsers actually send", async () => {
  // assets/js/forms.js posts `new FormData(form)`, which the browser encodes
  // as multipart/form-data, NOT urlencoded. The other tests here use
  // urlencoded, so without this one the encoding the site really uses would
  // have had no coverage at all.
  await captureMail(async (calls) => {
    const fd = new FormData();
    for (const [k, v] of Object.entries(VALID_WAITLIST)) fd.append(k, v);
    const request = new Request("https://www.aiatella.com/api/waitlist", {
      method: "POST",
      headers: { Origin: "https://www.aiatella.com", Accept: "application/json" },
      body: fd, // fetch sets multipart/form-data with a boundary
    });
    assert.match(request.headers.get("Content-Type"), /^multipart\/form-data; boundary=/);
    const res = await worker.fetch(request, makeEnv(), {});
    assert.equal(res.status, 200);
    assert.equal((await res.json()).redirect, "/waitlist-thanks.html");
    assert.ok(calls[0].body.text.includes("Aino Virtanen"));
    assert.ok(calls[0].body.text.includes("Terveystalo"));
  });
});

/* ------------------------------------------------- the case-sensitivity trap */

test("the real Message and Company fields are not read as honeypots", async () => {
  await captureMail(async (calls) => {
    const res = await post("/api/contact", VALID_CONTACT,
      { headers: { Accept: "application/json" } });
    assert.equal(res.status, 200);
    // Not flagged, and the visitor's own words are in the mail.
    assert.ok(!calls[0].body.subject.includes("possible spam"));
    assert.ok(calls[0].body.text.includes("clinical pilot"));
  });
});

test("a tripped honeypot is flagged but still delivered, so no lead is lost", async () => {
  await captureMail(async (calls) => {
    const res = await post("/api/contact", { ...VALID_CONTACT, message: "buy cheap pills" },
      { headers: { Accept: "application/json" } });
    assert.equal(res.status, 200);
    assert.equal(calls.length, 1, "flagged mail should still be sent");
    assert.match(calls[0].body.subject, /^\[possible spam\] /);
    assert.ok(calls[0].body.text.includes("message"));
    // The real message survived; the honeypot did not overwrite it.
    assert.ok(calls[0].body.text.includes("clinical pilot"));
    assert.ok(!calls[0].body.text.includes("cheap pills"));
  });
});

test("SPAM_MODE=drop bins the submission but still answers like a success", async () => {
  const env = makeEnv({ SPAM_MODE: "drop" });
  await captureMail(async (calls) => {
    const res = await post("/api/waitlist", { ...VALID_WAITLIST, website: "http://spam.example" },
      { env });
    assert.equal(res.status, 303, "a bot should not learn that it was caught");
    assert.equal(calls.length, 0, "no mail for a dropped submission");
  });
  assert.equal([...env.SUBMISSIONS.map.keys()].filter((k) => k.startsWith("sub:")).length, 0);
});

/* ---------------------------------------------------------- validation */

test("missing required fields come back as a per-field 422", async () => {
  const res = await post("/api/contact", { Name: "No Email Given" },
    { headers: { Accept: "application/json" } });
  assert.equal(res.status, 422);
  const body = await res.json();
  assert.equal(body.error, "validation_failed");
  assert.deepEqual(body.fields.map((f) => [f.field, f.error]).sort(),
    [["Email", "required"], ["Message", "required"]]);
});

test("an unparseable email address is rejected", async () => {
  const res = await post("/api/waitlist", { ...VALID_WAITLIST, Email: "aino at example" },
    { headers: { Accept: "application/json" } });
  assert.equal(res.status, 422);
  assert.deepEqual((await res.json()).fields, [{ field: "Email", error: "invalid_email" }]);
});

test("addresses with plus tags, subdomains and long TLDs are accepted", async () => {
  await captureMail(async () => {
    for (const email of ["a+waitlist@example.fi", "a@mail.example.co.uk",
      "onni.eriksson@aiatella.technology"]) {
      const res = await post("/api/waitlist", { ...VALID_WAITLIST, Email: email },
        { headers: { Accept: "application/json" } });
      assert.equal(res.status, 200, `rejected ${email}`);
    }
  });
});

test("an over-long message is rejected rather than truncated", async () => {
  const res = await post("/api/contact", { ...VALID_CONTACT, Message: "x".repeat(5001) },
    { headers: { Accept: "application/json" } });
  assert.equal(res.status, 422);
  assert.equal((await res.json()).fields[0].error, "too_long");
});

test("the radio value must be one of the four offered options", async () => {
  const res = await post("/api/waitlist", { ...VALID_WAITLIST, Radio: "Somewhere else" },
    { headers: { Accept: "application/json" } });
  assert.equal(res.status, 422);
  assert.equal((await res.json()).fields[0].error, "not_allowed");
});

test("optional fields may be omitted entirely", async () => {
  await captureMail(async (calls) => {
    const res = await post("/api/waitlist",
      { Name: "A", Email: "a@example.fi", Region: "Espoo" },
      { headers: { Accept: "application/json" } });
    assert.equal(res.status, 200);
    assert.ok(!calls[0].body.text.includes("Organization:"));
  });
});

/* -------------------------------------------------------------- redirects */

test("_next cannot be turned into an open redirect", async () => {
  await captureMail(async () => {
    const res = await post("/api/waitlist",
      { ...VALID_WAITLIST, _next: "https://evil.example/phish" });
    assert.equal(res.status, 303);
    assert.equal(res.headers.get("Location"), "/waitlist-thanks");
  });
});

test("_next cannot point at another page on the site either", async () => {
  await captureMail(async () => {
    const res = await post("/api/contact", { ...VALID_CONTACT, _next: "privacy.html" });
    assert.equal(res.headers.get("Location"), "/contact-thanks");
  });
});

/* --------------------------------------------------------- origin + method */

test("a post from an origin we do not know is refused", async () => {
  const res = await post("/api/contact", VALID_CONTACT,
    { headers: { Origin: "https://evil.example" } });
  assert.equal(res.status, 403);
  assert.equal((await res.json()).error, "forbidden_origin");
});

test("a post with no Origin header at all is allowed through", async () => {
  await captureMail(async () => {
    const request = new Request("https://www.aiatella.com/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(VALID_CONTACT),
    });
    const res = await worker.fetch(request, makeEnv(), {});
    assert.equal(res.status, 200);
  });
});

test("GET is rejected with an Allow header", async () => {
  const request = new Request("https://www.aiatella.com/api/contact");
  const res = await worker.fetch(request, makeEnv(), {});
  assert.equal(res.status, 405);
  assert.equal(res.headers.get("Allow"), "POST, OPTIONS");
});

test("an unknown form slug is a 404", async () => {
  const res = await post("/api/newsletter", VALID_CONTACT);
  assert.equal(res.status, 404);
});

test("a CORS preflight from an allowed origin is answered, others are not", async () => {
  const ok = await worker.fetch(new Request("https://www.aiatella.com/api/contact", {
    method: "OPTIONS", headers: { Origin: "https://www.aiatella.com" },
  }), makeEnv(), {});
  assert.equal(ok.status, 204);
  assert.equal(ok.headers.get("Access-Control-Allow-Origin"), "https://www.aiatella.com");

  const bad = await worker.fetch(new Request("https://www.aiatella.com/api/contact", {
    method: "OPTIONS", headers: { Origin: "https://evil.example" },
  }), makeEnv(), {});
  assert.equal(bad.status, 403);
});

/* ------------------------------------------------------- rate + failures */

test("a burst from one IP is throttled after five submissions", async () => {
  const env = makeEnv();
  await captureMail(async () => {
    const codes = [];
    for (let i = 0; i < 7; i++) {
      const res = await post("/api/waitlist", VALID_WAITLIST,
        { env, headers: { "CF-Connecting-IP": "203.0.113.9", Accept: "application/json" } });
      codes.push(res.status);
    }
    assert.deepEqual(codes, [200, 200, 200, 200, 200, 429, 429]);
  });
});

test("a mail failure with storage available still reports success", async () => {
  const real = globalThis.fetch;
  globalThis.fetch = async () => new Response("provider down", { status: 500 });
  try {
    const env = makeEnv();
    const res = await post("/api/contact", VALID_CONTACT,
      { env, headers: { Accept: "application/json" } });
    assert.equal(res.status, 200, "the lead is safe in KV, so do not alarm the visitor");
    assert.equal([...env.SUBMISSIONS.map.keys()].filter((k) => k.startsWith("sub:")).length, 1);
  } finally {
    globalThis.fetch = real;
  }
});

test("a mail failure with no storage configured reports failure to the visitor", async () => {
  const real = globalThis.fetch;
  globalThis.fetch = async () => new Response("provider down", { status: 500 });
  try {
    const res = await post("/api/contact", VALID_CONTACT,
      { env: makeEnv({ SUBMISSIONS: undefined }), headers: { Accept: "application/json" } });
    assert.equal(res.status, 502);
    assert.equal((await res.json()).error, "delivery_failed");
  } finally {
    globalThis.fetch = real;
  }
});

/* ----------------------------------------------------------- captcha hook */

test("Turnstile is only enforced when a secret is configured", async () => {
  const real = globalThis.fetch;
  globalThis.fetch = async (url) => {
    if (String(url).includes("turnstile")) {
      return new Response(JSON.stringify({ success: false }), { status: 200 });
    }
    return new Response(JSON.stringify({ id: "test" }), { status: 200 });
  };
  try {
    const off = await post("/api/contact", VALID_CONTACT, { headers: { Accept: "application/json" } });
    assert.equal(off.status, 200);

    const on = await post("/api/contact", VALID_CONTACT, {
      env: makeEnv({ TURNSTILE_SECRET: "secret" }),
      headers: { Accept: "application/json" },
    });
    assert.equal(on.status, 400);
    assert.equal((await on.json()).error, "captcha_failed");
  } finally {
    globalThis.fetch = real;
  }
});
