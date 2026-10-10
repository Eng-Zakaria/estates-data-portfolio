# Workshop exercises

*All data referenced here is synthetic: no real estate, building, person or compliance status is described.*

The three exercises for the 45-minute workshop. Each has the brief to read aloud, the task, and where the answers live. Answers for the facilitator are in the [answer key](answer-key.md).

## Exercise 1: three questions a number must answer

**Read aloud:** *Your Head of Estates asks for one number: "how much space do we have per person?" Write down the three questions you would ask before you answer.*

**Time:** 7 minutes, in pairs.

**Task:** for each candidate number, write the three questions.

| Candidate | Your three questions |
|---|---|
| Net internal area per staff full-time equivalent | |
| Booked hours per week | |
| Overdue inspections as at 31 March | |

**Answers:**

- Space per person: net or gross area? Staff, students, or both? Whole estate or only space tagged to a department?
- Booked hours: which rooms? Which weeks, and does a booking of one hour count as one booking or one hour? Double bookings?
- Overdue: measured against which date? Which inspections? Does an inspection with no record count as overdue or as compliant?

**Point to land:** the first question is always "what does this number measure". The registry answers it in one line, and the caveats answer the rest.

## Exercise 2: reading a dashboard without being misled

**Read aloud:** *You have the space utilisation and compliance reports in front of you. Three claims are made. For each one, say whether it is fair, and why.*

**Time:** 12 minutes, in the room with the reports.

**Task:** judge these three claims.

| Claim | Fair? | Why |
|---|---|---|
| "Teaching rooms in one building are 55% booked but only 21% full, so we should close some." | | |
| "We have no overdue safety inspections, so the estate is compliant." | | |
| "Total carbon fell this quarter, so the estate is on track for net zero." | | |

**Answers:**

1. **Partly.** The two numbers are measured from different sources: bookings from the timetable, group sizes from the booking record. Before closing a room, look at page 3 of the report for that room, and check whether the room is booked in large groups by design. "Frequency x occupancy" is a screening view, not an allocation decision.
2. **No.** A green cell can mean nothing was recorded. Check the as-of date and the inspection list for that building. Absence of a record is not evidence of compliance, and in the demo data the frequencies are examples rather than legal duties.
3. **No.** A single quarter can be weather. Check degree days, and check the pathway line, which uses a base year and a target year chosen by the owner. Emissions are location-based, so a tariff change is not in the numbers.

**Points to land:**

- Filters change every number on a page; never add totals from two filters.
- A blank is not a zero.
- Ask for the DQ score before quoting any of it.

## Exercise 3: how good is the data

**Read aloud:** *The quality scorecard says the meter datasets score in the eighties while everything else is above 95. What do you do with the carbon report this month?*

**Time:** 9 minutes, in pairs.

**Task:** answer these four in order.

1. Is the carbon report unusable, or usable with care?
2. Which number on the scorecard tells you the most, and why?
3. The meter score improved from 82 to 99 overnight. What are three possible explanations?
4. Someone says "the data quality is 99, so the carbon figure is right". What is wrong with that sentence?

**Answers:**

1. Usable with care. The low score comes from duplicate and misaligned half-hour rows that are quarantined, not lost. Check the failing-check table, and check whether the month has fewer periods than usual.
2. The score by dimension. A whole-dataset score hides whether completeness fell on one building or one field. The failing-check list tells you what actually broke.
3. The source started sending cleaner data; the pipeline fixed a rule; or the checks changed because a new check was added or removed. Compare like-for-like versions before celebrating.
4. The score measures the checks that exist. It cannot tell you that a definition is wrong, and it cannot see a field nobody checks.

**Point to land:** a score is a reason to ask what was checked, not a certificate.

## Exercise 4 (optional, for a half-day version)

**Read aloud:** *Your team must report space and carbon together. Someone asks for one table with both. What do you put in the grain line?*

**Answers:** the answer is "it depends what the table is for". For a building-level report, one row per building per month, with net internal area and whole-building area both named. Never mix the two areas in one column: that is the single most common mistake in estates reporting.
