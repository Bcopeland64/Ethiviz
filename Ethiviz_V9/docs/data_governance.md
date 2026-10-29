# EthiViz Data Governance and Partnership Intake

This document defines the minimum operational standards for prototype data and community-aligned translation work in EthiViz. It is intentionally scoped to the partnership infrastructure described in Upgrade 56: it sets the governance rules that make community-reviewed data possible, without claiming that any translation set is complete or authoritatively approved by a community.

V9 continues to treat all cultural prototypes and translations as draft material unless
their provenance, consent, and qualified human-review status are evidenced. The
operational job-retention defaults are documented separately in
[`compliance.md`](compliance.md); neither application deletion nor those defaults
establish community consent or erase external backups.

## Core principle

Translations and cultural prototypes are not merely model artifacts. They are claims about a community's moral and linguistic context. A prototype set may be useful as a draft, but it must not be treated as production-truth without provenance, consent, and review.

## Required provenance fields

Every prototype bundle should include a `translation_provenance` block with at least:

- `reviewed`: languages or entries that a fluent reviewer has explicitly checked
- `machine_generated`: languages or entries that were generated automatically and remain unreviewed
- `pending_review`: languages or entries waiting for a human review pass
- `reviewed_by`: mapping of language -> reviewer identity or handle
- `reviewed_at`: mapping of language -> ISO timestamp
- `community_consent`: a structured block describing whether the source language community has consented to the use of the material

The `community_consent` block should include at minimum:

- `status`: `approved`, `verified`, or `pending`
- `organization`: community or organization responsible for the data
- `contact`: contact or reference for follow-up
- `notes`: plain-language summary of consent or use terms

## Partnership gate

The following conditions are required before a language bundle can be treated as review-ready:

1. A named community or speaking organization is associated with the data.
2. Consent status is recorded explicitly.
3. The provenance keeps the distinction between machine-generated, reviewed, and unreviewed content.
4. Each language entry includes a review timestamp or identifies it as still pending review.

If any of these are missing, the system should treat the bundle as draft-only and surface a low-trust warning rather than an authoritative result.

## Operational use

- Use the `translation_provenance` block as the ground truth for trust scoring.
- Keep machine-generated and reviewed translations separate in the audit trail.
- Require community consent before a language bundle can be promoted to a production-facing recommendation.
- Treat this as the minimum governance layer for collaboration, not a substitute for community-led review.

## Review workflow

A fluent-language reviewer should perform the following checks:

- confirm the translation is faithful to the source wording and intent
- flag culturally inappropriate or mistranslated material
- record the reviewer identity and timestamp
- mark the bundle as reviewed only after the confirmation passes

## Failure mode to avoid

Machine translation without a consented provenance trail is not equivalent to a validated linguistic artifact. A generated bundle may help with exploratory work, but it must never be used as evidence of community-validated meaning without human review.
