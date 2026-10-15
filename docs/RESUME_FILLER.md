# RESUME FILLER bridge contract

The original extension is not modified. Your screenshot reports that its saved name and email are missing. AUTO WORK can read your existing local Python profile into its own saved profile; it cannot silently fix the extension's private Chrome storage.

## Input profile

AUTO WORK accepts either a flat object or an object with a `profile` field. Supported strings: `name`, `email`, `education`, `target`, `location`, `skills`, `experience`, `about`, `fillerURL`. `firstName`, `lastName`, `targetRole` and an array of skills are supported aliases on JSON import.

Example (fictional):

```json
{"schemaVersion":1,"profile":{"name":"Alex Example","email":"alex@example.com","education":"UC Berkeley","target":"Marketing internships","skills":["Content strategy","Audience research"],"experience":"Describe a real project and your actual contribution.","about":"I enjoy connecting creative ideas with measurable audience insight."}}
```

Exports contain `schemaVersion`, `source`, `exportedAt` and the complete supported `profile` object. Importing requires a preview click before replacing local profile facts. Empty names/emails remain empty. The app never infers eligibility, demographics, work authorization, GPA or claims from an employer's question.

## Existing tracker

In the local app, **Load existing tracker** reads `~/Desktop/RESUME FILLER/applications.csv` without modifying it. Set `RESUME_FILLER_APPLICATIONS` for another path. Only known submitted statuses become Applied. `submit_uncertain`, `needs_manual`, unsupported and unknown statuses become Saved, with the exact original status retained in notes. The import review explains this mapping. Exact company/role duplicates are skipped.

## Application intake

Use **Applications → Import RESUME FILLER jobs** with:

```json
{"applications":[{"company":"Example Company","role":"Marketing Intern","stage":"Applied","description":"The actual job description","url":"https://example.com/careers","notes":"Your application notes"}]}
```

Stages: Saved, Applied, Interview, Offer, Closed. Exact company/role duplicates are skipped on import. This is a local tracking operation, not application submission.

## Future extension import handler

Add an explicit “Import AUTO WORK profile” action to the extension's own settings page. The user selects the exported JSON, the extension validates known fields and displays a review screen, then the user confirms. Map only supported factual fields into its existing saved-profile schema. Do not map arbitrary keys or execute imported content. An exported AUTO WORK file has no API keys and cannot grant model access. The extension must still review unknown questions, attestation choices and submissions separately.

The current codebase for RESUME FILLER was inspected read-only for profile facts; its extension and running processes were not changed.
