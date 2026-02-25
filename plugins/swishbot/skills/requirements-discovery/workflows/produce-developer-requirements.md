# Produce Developer Requirements

Reverse engineer the technical layers from the scoped deliverable and produce an implementation-ready specification.

## Step 1: Reverse Engineer the Outcome

Once the output is clear, work backwards through the technical layers to determine what needs to be built.

- Does the output need a **new mart**? What entity does it represent?
- Does the mart need a **new fact or dimension**? What grain, what measures, what attributes?
- Do the facts/dimensions need **new staging models**? What source systems feed them?
- Do the sources need **new ingestion pipelines**? Is the data already in the warehouse?

Each layer you identify becomes a discrete unit of work.

## Step 2: Produce the Specification

The output of reverse engineering becomes the specification for the engineer. A complete spec includes:

- **Business context** — One paragraph on why this is being built
- **Output definition** — What the final deliverable looks like (grain, columns, filters, refresh cadence)
- **Source systems** — Where the data comes from
- **Technical layers** — What models/tables need to be created or modified at each layer
- **Acceptance criteria** — How the stakeholder will verify the deliverable is correct
- **Out of scope** — What was discussed but explicitly deferred

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
