# Compliance

**Question it answers:** which checks are late, which failed, and what needs doing this week?

**Refresh:** daily, from the inspection register. The report compares due dates with an as-of date you choose.

**Who to ask:** estates health and safety (frequencies, priorities, escalation); the analytics steward for definitions.

!!! warning
    The frequencies in the demo data are examples. They are not a statement of legal duty. In a real estate the compliance owner supplies every frequency from the legal source, and the register records where it came from.

## The five pages

| Page | What it shows | Read it when |
|---|---|---|
| 1. Executive red-amber-green grid | every building against every check type, coloured by status | you want the estate picture |
| 2. Overdue list | the checks that are late, with days overdue and contractor | you are dispatching work |
| 3. Next 90 days | a week-by-type grid of what is coming up | you are planning contractor capacity |
| 4. Remedial ageing | how long open fixes have been open | a fix is stuck and you need to know |
| 5. Trend | monthly late count and compliant share | you are reporting progress |

## How to read each measure

- **Total inspections** counts every check in scope, whatever its status.
- **Overdue count** counts checks past their due date with no recorded finish, measured against the as-of date.
- **Due within 30 days** counts checks falling due in the next 30 days from the as-of date. It is a workload signal, not a capacity forecast.
- **Failed with remedial open** counts failed checks that still have an open fix. This measure alone turns a cell red on page 1.
- **Days overdue** is days between the due date and the finish, or between the due date and the as-of date if still open. A negative number means it finished early.
- **Risk score** is a zero to four triage score that sorts the action list. It is not a legal risk rating.
- **Remedial ageing** counts days since a fix was raised and is still open.

## Common misreadings

1. **Green can mean "nothing recorded".** A building with no logged checks is green. That is the single most misread cell on this report.
2. **The as-of date changes the number.** Always say which date you used. "Overdue" without a date is not a fact.
3. **Overdue and failed are different lists.** A check can be completed and still failed. Page 2 and page 4 answer different questions.
4. **Ageing improves when old items are closed**, even if no new work was done. Read it with the open count.
5. **Risk scores are not comparable across check types.** Do not build a league table of contractors from them.
6. **Closure in the tracker is not verification on site.** A fix closed in the system may not have been done.
7. **Severity is not weighted.** A cosmetic fix and a safety fix age at the same rate.

## The escalation path this report supports

1. Page 2, filtered to more than 90 days: dispatch.
2. Page 4, filtered to more than 90 days on a failed check with an open fix: escalate to the compliance owner.
3. If the fix has no owner, that is the finding, not the number.

## Limitations to say out loud

- Frequencies are illustrative in the demo data.
- The register only knows what was entered. A check done and not logged is invisible.
- Remedial closure is a system state, not a site verification.
- Contractor names are for filtering and follow-up, not for scoring.

## Definitions and versions

Formulas, owners, versions and caveats are in the [metric registry](../generated/metric-registry.md). Words such as inspection, overdue and RAG status are in the [business glossary](../generated/glossary.md). The governance route for a serious finding is on the [governance framework](../governance/framework.md) page.