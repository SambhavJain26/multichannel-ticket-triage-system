# Maintenance pocket guide: editorial and visual decisions

## Format and purpose

Four 5.5 x 8.5-inch portrait pages, with no cover page. This is a separate alternative, not a replacement for the three-page Letter brief. The smaller page makes the text larger at a phone's fit-to-width view. Four pages separate the tangible output, behavior, proposed tools, and client fit without a dense diagram covering everything.

This is a reusable maintenance brief, not a personalized Angel brief or a COI document. Company and recipient remain placeholders. No research claim is invented. A personalized edition should substitute a verified relevance sentence for part of the introduction, not add another block.

## Reading order

1. **What your manager receives.** Name and recipient; plain-language purpose; an illustrative manager view with the leak, access/pet details, and available decisions; practical value; the human-control boundary. Lead with something concrete rather than a cover, feature list, or problem sermon.
2. **From report to approved action.** A single fictional leak request follows a numbered vertical actor/action sequence: resident report, one follow-up exchange, prepared context, manager decision, confirmed send. Explicitly note that safety alerts cannot wait for clarification and that sensitive/unclear cases need a person.
3. **What I would add.** Mark the diagram as a proposed client setup. Show existing channels/PMS feeding n8n, with message interpretation through OpenAI and durable history through PostgreSQL. Explain the return path for decisions and approved results; separate fixed safety rules from AI; identify client-server versus external-API hosting. Do not imply that the current demo already connects to a PMS.
4. **Fit with your business.** Three setup questions in dependency order: intake and identity, manager/PMS connection, client rules and ownership. State the actual local-demo tools and remaining client deployment work. End with a working-demo invitation and a clickable meeting link.

## Space priorities

The manager-view example and the request journey deserve the largest visual areas. Named software needs one clear diagram, not a logo wall or implementation inventory. Scope and limitations should be readable but should not displace the main story.

## Visual choices

- Illustrative manager view: makes the intended output tangible. It is explicitly labelled, not passed off as a screenshot of the running system.
- Numbered actor/action flow: demonstrates the clarification feature and the approval boundary through one coherent case. It replaces a generic workflow plus a repeated example underneath.
- Component/data connection map: explains each named tool's role and the information moving between them. Narrative below explains the return path and hosting split.
- Short prose: covers fit, constraints, and responsibilities. No table is needed for this amount of information.
- No screenshots in this edition: a desktop dashboard crop would either become too small or require another page. A future demo-evidence edition could replace the illustrative manager view with a verified, synthetic-data capture.

## What is deliberately omitted

No full failure-mode matrix, database schema, n8n node canvas, model-version comparison, configuration checklist, financial projections, pricing, implementation timeline, or claims of production reliability. Omit the before/after diagram because the output and running case communicate the change without repeating the story. Detailed integration API endpoints and operational support terms belong in implementation discussion. Important human approval and demo-versus-production distinctions stay in the brief.

## Phone and visual rules

Single reading column except the two short tool cards. Main text is approximately 12-15 pt, with larger 26 pt titles; minor labels are 9-11 pt. Text remains selectable. The page has a warm plain background, dark type, green for the added system, and restrained orange for editorial emphasis. No gradients. The PDF uses embedded fonts and vector shapes. Review full pages and a 390-pixel-wide render; font size alone is not a substitute for that review.

## Next conversation

One invitation: see one request in the demo and discuss the prospect's intake and PMS. No pressure language, invented urgency, or assumption that they are ready to buy.

## Evidence and scope

Content grounded in `docs/build-description.md`, `docs/production-maintenance-triage-blueprint.md`, and current decisions in `progress-notes.md`. The fictional example illustrates the proposed production operating model; it is not a customer result or evidence of a completed PMS integration. This artifact does not alter demo workflows or production scope.
