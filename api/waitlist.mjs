import { app } from "@azure/functions";
import { handleFormSubmission } from "./shared/forms.mjs";

app.http("waitlist", {
  methods: ["POST", "OPTIONS"],
  authLevel: "anonymous",
  route: "waitlist",
  handler: async (request, context) => {
    const result = await handleFormSubmission(request, "waitlist");
    return {
      status: result.status,
      headers: result.headers || {},
      jsonBody: result.body,
      ...(result.status === 303 ? { body: null } : {}),
    };
  },
});
