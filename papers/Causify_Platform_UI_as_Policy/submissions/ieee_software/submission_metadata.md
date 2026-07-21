# IEEE Software submission metadata

## Title

UI-as-Policy: Unified Permission and Layout System for Multi-Tenant Platforms

## Abstract

Multi-tenant SaaS products often carry a quiet interface contradiction. Backend policy changes, frontend conditionals lag behind, and users see buttons that return HTTP 403 or modules they cannot use. We present UI-as-Policy, a production-tested pattern that treats the UI as a policy surface. The backend materializes a tenant- and role-scoped contract; the web tier derives navigation, module visibility, layout, and client-side ability rules from it, while APIs still enforce authorization. Policy changes become reviewed data updates rather than redeploys. The paper defines the representation gap and a Truthful UX invariant for covered surfaces, then describes auditable view-as support workflows. In production, the system manages seven modules, 25+ permission subjects, 150+ layout fields, zero-deployment tenant onboarding, 73-100% coverage on high-value surfaces, 856 ms P50 full materialization, and 91% ETag revalidation hits.

## Keywords / tags

Multi-tenant SaaS; authorization; UI policy; server-driven UI; policy-as-data; impersonation; auditability; authorization drift.

## Three actionable practitioner insights

- Treat navigation, module visibility, and layout as an authorization surface. If the backend owns policy but the frontend guesses what to show, drift is only a matter of time.
- Materialize a tenant- and role-scoped UI contract on the server, then make the client consume that contract rather than reimplementing permission logic.
- Build support impersonation around immutable actor attribution, server-enforced allow-lists, signed effective context, and searchable audit logs; never use shared admin accounts as a shortcut.

## Upload checklist

- Paper PDF: `paper.pdf` or `Causify_Platform_UI_as_Policy_IEEE_Software.pdf`.
- Source files if requested: `paper.tex` and `references.bib`.
- Author photos: required by IEEE Software portal / CFP.
- Maximum references: 15.
- Abstract limit: 150 words.
- Word budget: 4,200 words including 250 words per figure/table; author bios and references excluded.
