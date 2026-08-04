import { app } from "@azure/functions";
import { handleFormSubmission } from "./shared/forms.mjs";

app.http("contact", {
  methods: ["POST", "OPTIONS"],
  authLevel: "anonymous",
  route: "contact",
  handler: async (request, context) => {
    const result = await handleFormSubmission(request, "contact");
    return {
      status: result.status,
      headers: result.headers || {},
      jsonBody: result.body,
      ...(result.status === 303 ? { body: null } : {}),
    };
  },
});
