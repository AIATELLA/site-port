import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { handleFormSubmission } from "../shared/forms.mjs";

function makeRequest(body, { method = "POST", contentType = "application/json", accept = "application/json" } = {}) {
  const headers = new Map([
    ["content-type", contentType],
    ["accept", accept],
    ["x-forwarded-for", "127.0.0.1"],
  ]);
  return {
    method,
    headers: { get: (k) => headers.get(k.toLowerCase()) || null },
    json: async () => body,
    formData: async () => {
      const entries = Object.entries(body);
      return { entries: () => entries };
    },
  };
}

describe("contact form", () => {
  it("accepts valid submission", async () => {
    const req = makeRequest({
      Name: "Test User",
      Email: "test@example.com",
      Message: "Hello world",
    });
    const result = await handleFormSubmission(req, "contact");
    assert.equal(result.status, 200);
  });

  it("rejects missing required fields", async () => {
    const req = makeRequest({ Name: "Test" });
    const result = await handleFormSubmission(req, "contact");
    assert.equal(result.status, 422);
    assert.ok(result.body.errors.Email);
    assert.ok(result.body.errors.Message);
  });

  it("rejects invalid email", async () => {
    const req = makeRequest({
      Name: "Test",
      Email: "not-an-email",
      Message: "Hello",
    });
    const result = await handleFormSubmission(req, "contact");
    assert.equal(result.status, 422);
    assert.ok(result.body.errors.Email);
  });

  it("honeypot: lowercase 'company' triggers silent accept", async () => {
    const req = makeRequest({
      Name: "Bot",
      Email: "bot@spam.com",
      Message: "Buy stuff",
      company: "spamcorp",  // lowercase = honeypot
    });
    const result = await handleFormSubmission(req, "contact");
    assert.equal(result.status, 200);
    assert.deepEqual(result.body, { ok: true });
  });

  it("real field: uppercase 'Company' is NOT a honeypot", async () => {
    const req = makeRequest({
      Name: "Real User",
      Email: "real@example.com",
      Message: "Genuine inquiry",
      Company: "Real Corp",  // uppercase = real field
    });
    const result = await handleFormSubmission(req, "contact");
    assert.equal(result.status, 200);
  });
});

describe("waitlist form", () => {
  it("accepts valid submission", async () => {
    const req = makeRequest({
      Name: "Test User",
      Email: "test@example.com",
      Region: "Helsinki",
    });
    const result = await handleFormSubmission(req, "waitlist");
    assert.equal(result.status, 200);
  });

  it("validates Radio field oneOf constraint", async () => {
    const req = makeRequest({
      Name: "Test",
      Email: "test@example.com",
      Region: "Helsinki",
      Radio: "InvalidOption",
    });
    const result = await handleFormSubmission(req, "waitlist");
    assert.equal(result.status, 422);
    assert.ok(result.body.errors.Radio);
  });
});

describe("unknown form", () => {
  it("rejects unknown form name", async () => {
    const req = makeRequest({ Name: "Test" });
    const result = await handleFormSubmission(req, "nonexistent");
    assert.equal(result.status, 400);
  });
});
