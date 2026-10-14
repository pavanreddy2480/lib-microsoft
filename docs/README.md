# Documentation Index

**New here? Start with [CONTEXT.md](CONTEXT.md)**: the one-page briefing on rules, decisions, architecture and how we work. Your own tasks are in [team/](team/).

The documents follow the delivery lifecycle a forward-deployed engineer runs with a client: understand the problem, pin down the rules, challenge them, specify, design, build, harden and pitch. Read them in order.

```
  DISCOVER          DEFINE              CHALLENGE         SPECIFY      DESIGN
  01 Problem   -->  03 Business   -->   05 Critique  -->  06 PRD  -->  07 Architecture
  02 Stake-         Rules               & Open                         08 Code Structure
     holders &      04 Assumptions      Questions                           |
     Workflows         & Scope                                              v
                                                                          BUILD
  PITCH             ITERATE             VERIFY            REVIEW       09 Development
  13 Pitch    <--   12 Iteration  <--   11 Test     <--   10 Edge  <--    Plan
                       Log                 Evidence          Cases
```

| # | Document | Stage | Answers the question | Owner | Status |
|---|---|---|---|---|---|
| - | [CONTEXT.md](CONTEXT.md) | Onboarding | "What do I need to know to start?" | P1 | ✅ |
| - | [problem-statement.pdf](problem-statement.pdf) | Source | "What did the client ask for?" | - | source |
| 01 | [Problem Statement](01-problem-statement.md) | Discover | What's broken, for whom, and what does success look like? | P1 | ✅ draft |
| 02 | [Stakeholders & Workflows](02-stakeholders-and-workflows.md) | Discover | Who uses it, what can each one do, what are the flows? | P1 | ✅ draft |
| 03 | [Business Rules](03-business-rules.md) | Define | What must always or never happen? Where is each rule enforced? | P1 | ✅ draft |
| 04 | [Assumptions & Scope](04-assumptions-and-scope.md) | Define | What did we assume? What's in and out? How is the seed data read? | P1 | ✅ draft |
| 05 | [Critique & Open Questions](05-critique-and-open-questions.md) | Challenge | What's ambiguous or risky? Where is our design weak? | P1 | ✅ draft |
| 06 | [PRD](06-prd.md) | Specify | Functional requirements, refusals, NFRs, acceptance criteria, screens | P1 | ✅ draft |
| 07 | [Architecture](07-architecture.md) | Design | How is it built, and why? What are the trade-offs? | P7 | ✅ draft |
| 08 | [Code Structure](08-code-structure.md) | Design | Where does each piece of code live? What are the conventions? | P1 | ✅ |
| 09 | [Development Plan](09-development-plan.md) | Build | Who builds what, in which order, and by when? | P1 | ✅ |
| 10 | [Edge Cases](10-edge-cases.md) | Review | What awkward situations must be handled, and how is each tested? | P7 / P4 | ✅ draft |
| 11 | [Test Evidence](11-test-evidence.md) | Verify | What did we actually run, and what were the results? | P7 | ⏳ after build |
| 12 | [Iteration Log](12-iteration-log.md) | Iterate | What changed, what did we catch, how did we use AI? | P1 + all | ✅ ongoing |
| 13 | [Pitch](13-pitch.md) | Pitch | The 2-slide consulting pitch + demo script | P1 | P1 |

**Rule IDs used across all docs:** `BR` business rule (PDF) · `PR` policy rule (ours) · `IR` integrity rule (DB) · `A` assumption · `T` trade-off · `W` known weakness · `E` edge case · `O` open edge case · `I` iteration log entry.
