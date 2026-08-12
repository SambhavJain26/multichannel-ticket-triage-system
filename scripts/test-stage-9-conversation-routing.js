const fs = require("fs");

function loadWorkflow(name) {
  return JSON.parse(fs.readFileSync(`workflows/${name}`, "utf8"));
}

function nodeCode(workflow, name) {
  const found = workflow.nodes.find((node) => node.name === name);
  if (!found?.parameters?.jsCode) throw new Error(`Missing Code node: ${name}`);
  return found.parameters.jsCode;
}

function run(code, values) {
  global.$input = {all: () => values.map((json) => ({json}))};
  return new Function(code)();
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const tenant = loadWorkflow("maintenance-triage-tenant-telegram.json");
const intake = loadWorkflow("maintenance-triage-tenant-intake.json");
const manager = loadWorkflow("maintenance-triage-manager-desk.json");
const recordStatusNode = tenant.nodes.find((node) => node.name === "Postgres Record Status Reply");
assert(recordStatusNode?.parameters?.query?.includes("'inbound', 'status'"), "Status audit uses an intent outside the database contract.");

const openTickets = [
  {id: 12, ref: "MR-0012", issue_summary: "Door hinge squeaks", vendor_status: "AWAITING_VENDOR"},
  {id: 11, ref: "MR-0011", issue_summary: "Ceiling fan stopped working", vendor_status: "SENT"},
];
const routeCode = nodeCode(tenant, "Route Tenant Message");
const statusRoute = run(routeCode, [{
  chat_id: "demo-chat",
  message_id: "38",
  text: "can you tell me when will all these issues be resolved??",
  ticket: openTickets[0],
  open_tickets: openTickets,
}]);
assert(statusRoute.length === 1 && statusRoute[0].json.route === "status", "Multi-request status question created a new request.");

const newIssueRoute = run(routeCode, [{
  chat_id: "demo-chat",
  message_id: "39",
  text: "also I have another issue - the kitchen tap is leaking",
  ticket: openTickets[0],
  open_tickets: openTickets,
}]);
assert(newIssueRoute[0].json.route === "new", "A distinct maintenance issue did not create a new request.");

const statusCode = nodeCode(tenant, "Prepare Tenant Status Reply");
const statusReply = run(statusCode, [statusRoute[0].json]);
assert(statusReply.length === 1, "A status question produced more than one tenant reply.");
const statusText = statusReply[0].json.message_text;
assert((statusText.match(/MR-0011/g) || []).length === 1, "MR-0011 is missing or duplicated in the consolidated status reply.");
assert((statusText.match(/MR-0012/g) || []).length === 1, "MR-0012 is missing or duplicated in the consolidated status reply.");

const normalizeEmail = nodeCode(intake, "Normalize Email Intake");
const ignoredVendorEmail = run(normalizeEmail, [{
  subject: "[MT-SYSTEM][VENDOR] Maintenance request - Maple Court, Unit 2B",
  from: {value: [{address: "sambhavn8n@gmail.com"}]},
  text: "Could you please take a look at Maple Court, Unit 2B?",
}]);
assert(ignoredVendorEmail.length === 0, "A system vendor email can re-enter IMAP triage.");

const tenantEmail = run(normalizeEmail, [{
  subject: "Leaking tap",
  from: {value: [{address: "tenant@example.com"}]},
  text: "The kitchen tap is leaking.",
  messageId: "tenant-message-1",
}]);
assert(tenantEmail.length === 1 && tenantEmail[0].json.from_address === "tenant@example.com", "Structured IMAP sender address was not normalized.");

const vendorEmailCode = nodeCode(manager, "Prepare Vendor Email");
const vendorEmail = run(vendorEmailCode, [{
  result: "send",
  attempt: {manager_chat_id: "manager", vendor_email: "vendor@example.com"},
  ticket: {id: 11, ref: "MR-0011", body_raw: "Property: Maple Court", unit_identifier: "2B", issue_summary: "Ceiling fan stopped working"},
  system_mail: {vendor_subject_prefix: "[MT-SYSTEM][VENDOR]"},
}]);
assert(vendorEmail[0].json.email_subject.startsWith("[MT-SYSTEM][VENDOR] "), "Vendor email is missing the shared-mailbox loop marker.");

const vendorUpdateCode = nodeCode(manager, "Prepare Tenant Vendor Update");
const vendorUpdate = run(vendorUpdateCode, [{
  result: "sent",
  ticket: {id: 11, ref: "MR-0011", tenant_chat_id: "demo-chat", issue_summary: "Ceiling fan stopped working."},
}]);
assert(vendorUpdate.length === 1 && vendorUpdate[0].json.message_text.includes("MR-0011") && vendorUpdate[0].json.message_text.includes("Ceiling fan"), "Tenant vendor update is not request-specific.");

console.log("OK: status questions consolidate open requests and system vendor emails cannot loop into intake");
