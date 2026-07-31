/**
 * Progressive enhancement for the waitlist and contact forms.
 *
 * The forms work without this file: they carry a real method/action, so a
 * plain POST reaches the Worker and the Worker answers with a 303 to the
 * thank-you page. What this adds is submitting in place -- a busy state, a
 * spoken status message, field-level errors from the server, and no
 * full-page navigation until the submission has actually succeeded.
 *
 * Framer's own form runtime did not survive the static export, which is
 * why this exists at all.
 */
(function () {
  "use strict";

  var MESSAGES = {
    required: "This field is required.",
    invalid_email: "Please enter a valid email address.",
    too_long: "This answer is too long.",
    not_allowed: "Please choose one of the listed options.",
  };

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var forms = document.querySelectorAll("form[data-form]");
    for (var i = 0; i < forms.length; i++) enhance(forms[i]);
  });

  function enhance(form) {
    // One live region per form, created here rather than in the markup so
    // the two form pages stay free of anything this feature owns. It goes
    // directly after the submit button where the eye already is, not at the
    // end of the form -- the end is where the privacy note lives.
    var status = document.createElement("div");
    status.className = "form-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.hidden = true;
    var buttons = form.querySelectorAll('button[type="submit"]');
    var anchor = buttons.length ? outermostContainer(form, buttons[buttons.length - 1]) : null;
    if (anchor) anchor.parentNode.insertBefore(status, anchor.nextSibling);
    else form.appendChild(status);

    form.addEventListener("submit", function (event) {
      // Let the browser's own required/type=email checks run first; they
      // are better localised than anything written here.
      if (typeof form.checkValidity === "function" && !form.checkValidity()) {
        if (typeof form.reportValidity === "function") form.reportValidity();
        return;
      }
      if (!window.fetch || !window.FormData) return; // fall back to a real POST
      event.preventDefault();
      submit(form, status);
    });
  }

  /**
   * Walk up from a submit button to the last ancestor that is still a
   * direct descendant chain of the form. Framer wraps each button in a
   * breakpoint container, so inserting next to the button itself would put
   * the status line inside that wrapper.
   */
  function outermostContainer(form, el) {
    var node = el;
    while (node.parentNode && node.parentNode !== form) node = node.parentNode;
    return node.parentNode === form ? node : null;
  }

  function submit(form, status) {
    clearErrors(form);
    setBusy(form, true);
    say(status, "working", "Sending…");

    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" },
    })
      .then(function (res) {
        return res.json().then(
          function (data) { return { res: res, data: data }; },
          function () { return { res: res, data: {} }; }
        );
      })
      .then(function (out) {
        var res = out.res, data = out.data;
        if (res.ok && data.redirect) {
          say(status, "ok", "Thank you — taking you to the next page…");
          window.location.assign(data.redirect);
          return;
        }
        setBusy(form, false);
        if (res.status === 422 && data.fields && data.fields.length) {
          showErrors(form, data.fields);
          say(status, "error", "Please check the highlighted fields.");
          return;
        }
        if (res.status === 429) {
          say(status, "error", "Too many attempts just now. Please try again in a minute.");
          return;
        }
        say(status, "error", fallbackMessage());
      })
      .catch(function () {
        setBusy(form, false);
        say(status, "error", fallbackMessage());
      });
  }

  /** Matches the address in the site footer, so the two never disagree. */
  function fallbackMessage() {
    return "Sorry, something went wrong sending that. Please try again, or email us at " +
      "Contact@aiatella.com.";
  }

  function setBusy(form, busy) {
    form.setAttribute("aria-busy", busy ? "true" : "false");
    // Both breakpoint copies of the submit button live in the form, so
    // disable every one of them, not just the visible one.
    var buttons = form.querySelectorAll('button[type="submit"]');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].disabled = busy;
      buttons[i].style.opacity = busy ? "0.6" : "";
      buttons[i].style.cursor = busy ? "progress" : "";
    }
  }

  function field(form, name) {
    var el = form.elements[name];
    if (!el) return null;
    return el.length && !el.tagName ? el[0] : el; // RadioNodeList -> first input
  }

  function showErrors(form, fields) {
    var first = null;
    for (var i = 0; i < fields.length; i++) {
      var el = field(form, fields[i].field);
      if (!el) continue;
      el.setAttribute("aria-invalid", "true");
      var note = document.createElement("p");
      note.className = "form-field-error";
      note.textContent = MESSAGES[fields[i].error] || "Please check this field.";
      var wrapper = el.closest("label") || el.parentNode;
      wrapper.parentNode.insertBefore(note, wrapper.nextSibling);
      if (!first) first = el;
    }
    if (first && typeof first.focus === "function") first.focus();
  }

  function clearErrors(form) {
    var notes = form.querySelectorAll(".form-field-error");
    for (var i = 0; i < notes.length; i++) notes[i].parentNode.removeChild(notes[i]);
    var flagged = form.querySelectorAll('[aria-invalid="true"]');
    for (var j = 0; j < flagged.length; j++) flagged[j].removeAttribute("aria-invalid");
  }

  function say(status, state, text) {
    status.hidden = false;
    status.setAttribute("data-state", state);
    status.textContent = text;
  }
})();
