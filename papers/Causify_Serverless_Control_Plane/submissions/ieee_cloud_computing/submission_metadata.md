# IEEE Cloud Computing submission metadata

## Title

Serverless Control Plane, Container Data Plane: A Governance Boundary for Multi-Tenant AI Platforms

## Abstract

Multi-tenant AI platforms often spread governance through every service. One handler validates identity, another trusts a schema prefix, and a generated API spec exposes modules a tenant never licensed. We present a production pattern that moves identity materialization, tenant scope derivation, module gating, API-surface filtering, and auditable view-as support into a serverless control plane. Container workloads on Kubernetes, Lambda-backed modules, and Fargate jobs execute only inside injected scope. In eight months at Causify AI, the pattern concentrated shared governance in a 135-line Lambda middleware spine, covered 12 data-plane services, moved five of six tenant lifecycle operations out of deployments, and reduced visible API surface by 67-90% for limited-module tenants. Full materialization was 856 ms P50; ETag revalidation handled 91% of steady-state traffic at 68 ms P50.

## Keywords / tags

Multi-tenant SaaS; AI platform; serverless architecture; control plane; data plane; scope injection; API governance; authorization; Kubernetes; AWS Lambda.

## Practitioner takeaways

- Move tenant scope derivation into one control plane; do not ask every service to rediscover tenant truth.
- Treat API surface as governed output. Filter generated specs and direct requests by the effective tenant's licensed modules.
- Keep container workloads simple: execute inside injected scope, log the scope envelope, and reject missing scope at every boundary.

## Upload checklist

- Paper PDF: `paper.pdf` or `Causify_Serverless_Control_Plane_IEEE_Cloud_Computing.pdf`.
- Source files if requested: `paper.tex` and `references.bib`.
- Maximum references: keep at or below 15 for magazine submission.
