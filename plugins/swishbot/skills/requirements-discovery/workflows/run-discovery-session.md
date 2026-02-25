# Run Discovery Session

Guide a stakeholder from a vague idea to a scoped, concrete deliverable through structured questioning.

## Step 1: Understand the Request

Start by understanding what the stakeholder wants and why they want it. Ask open-ended questions about the business problem, not the technical solution.

- **Ask what and why, not how.** "What decision will this help you make?" not "Do you want a dashboard or a report?"
- **Redirect solution-jumping.** When a stakeholder says "I need a Snowflake table that..." — stop. Back up. What business question are they trying to answer?
- **Identify the trigger.** What changed? Why now? Understanding urgency and context reveals the real requirement.

## Step 2: Plan Right-to-Left

Determine the desired end state first, then work backwards to identify the minimum viable deliverables.

- **Start from the output.** What does the stakeholder want to see? A number on a screen? A filtered list? A daily email? A self-serve dashboard?
- **Define the grain.** What does one row represent in their ideal output? One customer? One transaction? One day?
- **Identify the consumers.** Who will use this? How often? What decisions does it drive?

## Step 3: Narrow the Scope

Output-led development. Identify a single deliverable. If it sounds like five projects, it probably is.

Common triggers that indicate a single, scoped deliverable:

- **Existing report/dashboard/spreadsheet** — "We already have this in Excel, but..." means you are replicating and improving a known output.
- **Overly manual process** — "Every Monday someone pulls data from three systems and..." means you are automating a known workflow.
- **New desired dataset** — "We want to start tracking..." means you are building something net-new with a clear boundary.

If the request does not fit one of these patterns, break it down until each piece does.

## Step 4: Separate People/Process from Technology

Not all problems are solved with a new pipeline. Ask questions to surface process issues before proposing technical solutions.

- **"Who does this today?"** — If nobody does it, why not? Is it a data problem or a process problem?
- **"What happens with the output?"** — If nobody acts on it, the deliverable has no value regardless of how well it is built.
- **"What would change if you had this tomorrow?"** — If the answer is vague, the requirement is not ready.

## Conversation Guidelines

During the intake conversation with the stakeholder:

- **Ask pertinent follow-up questions.** Each question should move the conversation toward a concrete deliverable. Avoid asking questions you can answer yourself from context.
- **Do not let the stakeholder get off track.** When the conversation drifts to tangential topics, acknowledge the point and redirect: "That is a great point — let us park that for a future phase and stay focused on [current deliverable]."
- **Keep scope focused.** If the stakeholder introduces a new requirement mid-conversation, explicitly call it out: "That sounds like a separate deliverable. Should we finish scoping [current item] first?"
- **Summarize understanding back at each stage.** Before moving to the next step, confirm: "So what I am hearing is [summary]. Is that right?" Do not assume — verify.
- **Use the stakeholder's language.** Avoid technical jargon unless the stakeholder uses it first. Mirror their terminology.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
