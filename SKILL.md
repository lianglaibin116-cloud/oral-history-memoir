---
name: oral-history-memoir
description: Plan, produce, audit, and deliver evidence-based family oral-history memoirs from recorded interviews. Use for consent and scope design, interview preparation, speaker-aware transcription, source-linked fact management, restrained memoir writing, privacy review, and print-ready Word/PDF delivery. Do not use for fictional biographies or for inventing missing life events.
---

# Oral History Memoir

Turn real interviews into a traceable, respectful, print-ready family memoir. Treat the narrator's account and permissions as the controlling source; a payer or family member cannot override the narrator's expressed wishes.

## Start with an inventory

Before editing or generating content:

1. Inspect the project files and classify them as consent, original audio, raw ASR, reviewed transcript, evidence, draft, QA, or production files.
2. Preserve original audio and raw ASR as read-only evidence. Never silently replace them with cleaned versions.
3. Identify only choices that materially change the result: narrator name or pseudonym, verified birth year, intended audience, private versus public use, target length, available media, and permitted editing level.
4. Record conflicts, missing facts, unclear speakers, and privacy-sensitive material before drafting.

If the project has no structure, run `scripts/scaffold_project.py`. Read [workflow.md](references/workflow.md) for stage gates and folder meanings.

## Work through the gates

Follow this order unless the user explicitly scopes the task to one stage:

1. Confirm continuing consent and service boundaries.
2. Record or ingest interviews without altering originals.
3. Transcribe, diarize, and human-review speaker labels.
4. Build source-linked facts, quotations, conflicts, and follow-up questions.
5. Draft chapters from confirmed evidence only.
6. Audit facts, privacy, chronology, names, direct quotations, and unresolved markers.
7. Obtain narrator/client approval of the manuscript.
8. Produce A5 Word/PDF or the agreed format, render every page, proof one physical copy, and obtain print sign-off.
9. Deliver approved files and apply the agreed retention/deletion plan.

Do not automate past a human gate. Continuing consent, disputed facts, sensitive third-party material, narrator approval, and print-proof approval require a person to decide.

## Preserve evidence and truth

Apply the rules in [editorial-and-evidence.md](references/editorial-and-evidence.md):

- Do not invent dates, places, actions, weather, clothing, motives, inner thoughts, dialogue, or causal explanations.
- Write uncertain dates and amounts approximately. Keep conflicting accounts visible until resolved.
- Use quotation marks only for wording confirmed against source audio or an approved transcript.
- Separate personal memory from externally sourced historical background.
- Label inference as inference; omit it when it adds no necessary value.
- Never convert automatic labels such as `Speaker 0` into named people without human confirmation.
- Do not draft from raw ASR alone when reviewed transcripts or evidence cards are available.

Lightly improve structure, clarity, repetition, and spoken-language fragments. Keep the narrator's tone warm, plain, and credible; avoid sensational or heroic exaggeration.

## Route to the relevant reference

- For full stage order, inputs, outputs, and human approvals, read [workflow.md](references/workflow.md).
- For recording, diarization, speaker mapping, transcript review, and follow-up interviews, read [interview-and-transcription.md](references/interview-and-transcription.md).
- For fact ledgers, source hierarchy, chapter writing, quotations, uncertainty, and editorial QA, read [editorial-and-evidence.md](references/editorial-and-evidence.md).
- For DOCX/PDF layout, A5 defaults, image quality, rendering, proofing, and delivery packaging, read [production-and-delivery.md](references/production-and-delivery.md).
- For consent, client/narrator roles, privacy, service claims, data handling, and commercial boundaries, read [commercial-and-consent.md](references/commercial-and-consent.md).

Use only the references needed for the current stage.

## Use the included tools

Resolve script paths relative to this skill directory, not the user's working directory. Python 3.10+ is recommended; the two helpers use only the standard library and do not make network requests. Create client workspaces outside this public repository.

Create a new project:

```bash
python3 scripts/scaffold_project.py /path/to/project --project-id MEM-YYYY-NNN --title "回忆录项目"
```

Audit a project stage:

```bash
python3 scripts/audit_project.py /path/to/project --phase final --final /path/to/manuscript.docx
```

The audit checks structure and detectable risks; it cannot prove that a story is true or that consent is valid. A human must review source audio, permissions, and sensitive decisions. `setup` checks only the initial structure. For text checks supply DOCX, Markdown, or TXT; PDF needs separate extraction and visual review. A `pass` is not approval to print or publish.

For structured transcript exchange, use [memoir-transcript.schema.json](assets/memoir-transcript.schema.json). The project auditor does not validate this schema; validate it separately and check speaker references, unique IDs, and end times greater than start times in application code.

## Produce commercial documents carefully

When creating or changing DOCX, use the available document-production skill and its render-and-verify workflow. When creating or inspecting PDF, use the available PDF skill. Do not claim a file is print-ready until all pages have been rendered and visually inspected.

Treat A5, 12–13 pt body text, at least 1.45 line spacing, and 300 dpi images as useful family-edition defaults, not universal requirements. The signed specification wins.

## Report completion

At handoff, state:

- exact output paths;
- what was created or changed;
- verified word/character count and page count when available;
- which checks passed;
- every unresolved fact, privacy decision, missing permission, or print-risk;
- the next required human approval.

Keep internal evidence, QA reports, and working files separate from the client-facing delivery package.
