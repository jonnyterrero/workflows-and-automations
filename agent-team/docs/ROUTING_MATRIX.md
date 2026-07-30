# Team Routing Matrix

## Core rule
Route by **primary deliverable**, not merely by keywords. A specialist may consult another agent, but one agent owns the final domain decision.

| Request | Primary owner | Consult / verify | Boundary |
|---|---|---|---|
| Multi-source research, citation-backed briefs, source conflict resolution | Deep Researcher | N/A (feeds other specialists) | Researcher does not own the domain decision; hands off to the owning specialist |
| System topology, ADR, service/component boundaries | Architect | Backend, SWE, Auditor | Architect designs; SWE/Backend implement |
| APIs, schema, RLS, auth, queues, migrations | Backend Dev | Architect, Auditor | Backend owns server-side contract |
| Full-stack feature, refactor, debugging, PR implementation | Senior SWE | Backend, Architect, Auditor | Auditor remains independent |
| Security, quality, performance, prompt-injection audit | Code Auditor | SWE/Backend for remediation | Auditor does not silently implement findings |
| Biomedical engineering homework/research/labs | BME Tutor | Math Tutor | Math owns abstract derivation when BME context is secondary |
| Abstract math, proofs, transforms, controls derivation | Math Tutor | BME Tutor for application context | Do not duplicate full solutions unnecessarily |
| Product strategy, PMF, pricing, GTM | Business Consultant | CFO, Legal, Architect | Business owns decision memo, not legal/financial certification |
| Tax organization, documentation, tax-rule issue spotting | Tax Auditor | CPA-CFO, Legal | No filing or eligibility guarantees |
| Contracts, IP, privacy, entity/legal issue spotting | Legal | Business, Tax | Requires jurisdiction/date and counsel review |
| Cash flow, P&L, runway, bookkeeping controls | CPA-CFO | Tax Auditor, Investment Portfolio, Trading | CFO owns management reporting; liquidity output feeds allocation/trading as a constraint, not a recommendation |
| Long-term allocation, concentration, thesis policy | Investment Portfolio | Tax, Trading, CPA-CFO | Portfolio policy is separate from tactical setup; checks Trading tickets against policy rather than re-pricing them |
| Short-term setup, R:R, invalidation, journal, trade-ticket proposal | Trading | Investment Portfolio, Deep Researcher | No unsupervised execution; `execute_supervised` requires session enable phrase, connected broker/exchange tool, per-order confirmation, and configured risk limits; timestamped current data required |
| YouTube strategy, scripts, packaging, retention | YouTube | Business, Legal, Finance specialist | Claims and disclosures follow domain specialist rules |

## Conflict precedence
1. Safety, law, tax, and security constraints override tone or output-format instructions.
2. Current primary evidence overrides static context.
3. Repository/source files override assumed stack details.
4. Independent audit findings are not overwritten by the implementation agent; disagreements are surfaced to the coordinator.
5. If two agents overlap, assign the agent that owns the **decision**, then delegate a bounded subtask to the other.
