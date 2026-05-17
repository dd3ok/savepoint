# Changelog

All notable changes to this repository are documented here.

## v1.0.0 - 2026-05-11

- Require prompt-ready handoffs to include embedded resume prompt evidence.
- Clarify resume lookup and cleanup ordering in `SKILL.md`.
- Default generated handoffs to `.new-session-handoff/HANDOFF.md` with an embedded `## Resume Prompt`.
- Keep prompt-only output and detail templates out of the default skill-package artifact set.
- Add verified-resume cleanup policy for deleting only untracked generated handoff artifacts.
- Tighten marker validation so written `HANDOFF_READY` values must be absolute `HANDOFF.md` paths.
- Remove legacy marker/checklist/expanded reference stubs and centralize marker semantics in `handoff-contract.md`.
- Add Korean README usage examples and preserve Korean invocation phrases in skill frontmatter validation.
- Add shared marker cross-field validation used by portable and repository validators.
- Add repository validation scripts, staleness rules, and MIT license files.
- Add a four-line `TL;DR / Operational Summary` requirement to handoff manifests.
- Reframe `HANDOFF.md` as a recoverable entry manifest rather than a forced full summary.
- Add focused expanded handoff artifact guidance for large architecture or multi-file work.
- Add strict `SAFE_FOR_NEW_SESSION` quality checklist and versioned automation marker semantics.
- Add manual eval scenarios for compact, expanded, prompt-only, resume-mismatch, validation-status, and secret-redaction flows.
- Add compact, expanded, and unsafe handoff examples.
- Add security guidance for redacting secrets from handoff artifacts.
- Clarify validation marker semantics and expanded artifact path conventions.
- Expand the architecture handoff example with realistic boundary and changed-file detail.
- Enrich expanded validation and pitfalls examples and expand README release documentation.
- Quote skill frontmatter description and add a YAML frontmatter eval.
