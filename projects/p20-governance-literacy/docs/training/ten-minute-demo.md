# 10-minute demo script

For someone who has never opened the dashboards. Ten minutes, one screen, one story.

**Before you start:** have the space utilisation report and the data quality scorecard open in two tabs. Know your as-of date. Have the glossary open in a third tab.

## 0:00 to 0:30 - Set the scene

> "Everything here runs on made-up data. The buildings are invented. What is real is the method: how a number is defined, how you check it, and how you read it."

Say this out loud. It prevents the most common misunderstanding later.

## 0:30 to 2:00 - The three questions

Open the space utilisation report, page 1. Point at the cards.

> "Three numbers. Frequency: how often a room is booked. Occupancy: how full it is when booked. Utilisation: the two multiplied. Here is the catch: utilisation is a product, not a time average. A room booked once for fifty people scores the same as a room booked every day at half full. So always look at frequency and occupancy as well."

Change the building slicer. Show the bar moving.

> "Filters change every number on the page. Never add totals from two filters and call it the estate."

## 2:00 to 4:00 - Ask the audience

> "Look at page 3, rooms to review. Sorted worst first. What do you notice?"

Let them answer. Usually: "some rooms are barely used" or "there are blanks".

> "The blanks are the point. A blank means no data, not zero. A room with no bookings and a room with no sensor cover look the same in a chart, and they need different actions."

## 4:00 to 6:00 - The quality question

Switch to the data quality scorecard.

> "Before you trust a number, look at how good the data is. Most datasets score above 95. The meter files score in the eighties, because they arrive with duplicate and misaligned readings that the pipeline puts in quarantine rather than passing on. That is what you want: bad rows held back with a reason, not quietly averaged in."

> "Remember: the score measures the checks we wrote. A check nobody wrote cannot fail."

## 6:00 to 8:00 - Where a number comes from

Open the lineage page. Trace one card back through the diagram.

> "Every number has a path. Booked hours come from the timetable, get cleaned, join to the calendar, and land in one analysis table that the dashboard reads. You can follow it in two clicks. If you cannot follow it, that is a governance problem, not your problem."

## 8:00 to 9:30 - The one rule that matters most

> "If you quote a number, quote the definition and the date with it. 'Overdue as at 31 March' is a fact. 'Overdue' on its own is not. That single habit prevents most of the arguments about data."

## 9:30 to 10:00 - Close

> "Two places to go: the dashboard guide says how to read each report and what people get wrong. The glossary says what every word means. If a number looks wrong, tell the steward. Please do not work around it."

## If you are asked a question you cannot answer

Say so, and say where the answer lives. "I do not know. It is in the metric registry under that name, and if it is not, that is a gap I will raise today." Then actually raise it, through the [data request process](../process/data-request.md).