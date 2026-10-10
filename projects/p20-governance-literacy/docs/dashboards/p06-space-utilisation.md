# Space utilisation

*All data referenced here is synthetic: no real estate, building, person or compliance status is described.*

**Question it answers:** which rooms are booked, which rooms are used, and what could we do differently?

**Refresh:** monthly, from the academic calendar and the timetable feed. Booked hours come from the timetable; occupancy comes from group sizes on the booking.

**Who to ask:** estates planning (space allocation and targets); the analytics steward for definitions.

## The five pages

| Page | What it shows | Read it when |
|---|---|---|
| 1. Executive overview | the main cards plus bars by building and a weekly trend | you want the state of the estate in one screen |
| 2. Heatmap | when rooms are in use, by day and hour | you are arguing about evening or weekend use |
| 3. Rooms to review | a table of rooms with the numbers that matter, sorted worst first | you are picking rooms for action |
| 4. Department allocation | space per full-time staff compared with the middle department | a department asks for more space |
| 5. What-if | what could be released at a target use rate | you are planning an estates strategy |

Slicers at the top of each page: building, type of room, teaching week. Use them before you read any number.

## How to read each measure

- **Frequency %** is booked hours divided by the hours a room could have been used. It says how often the room is booked, not how full it is.
- **Avg Occupancy %** is the average group size compared with the seats in the room. It says how full the room is when it is booked.
- **Utilisation %** is frequency times occupancy. It tries to answer "how much is this room used" in one number.
- **No-show %** is events where sensors saw nobody in the room during the event. Events with no sensor cover are left out of the count.
- **m2 per Staff FTE** is net internal area divided by full-time staff. The middle department is used as the benchmark, not the average, so one big department cannot drag the line.
- **Releasable m2** is a what-if number. It uses the target you choose. It is not a saving, and it costs nothing to compute.

## Common misreadings

1. **Utilisation is a product, not a time average.** A room booked once for fifty people scores like a room booked daily for half a room. Read frequency and occupancy as well.
2. **Low frequency does not always mean a bad room.** A rarely opened seminar room with a few big bookings will look terrible on this score.
3. **A green room may have no data.** If a room has no events, the table shows a blank, not a zero. Blank means "we have nothing to say", not "unused".
4. **No-show % moves when sensors are added.** The measure only counts events with cover, so adding sensors can change the number for reasons that have nothing to do with students.
5. **Space per FTE leaves out untagged space.** Only space tagged to a department is counted, so the estate total is lower than a floor walk suggests.
6. **The group size is from the booking, not the room.** Observed headcounts come from sensors and are a different measure. The two will not match.

## Limitations to say out loud

- Both inputs are proxies. Timetable data says what was booked, not what happened.
- Evening and weekend use is mostly missing from the timetable.
- Releasable area ignores decant cost, shared space and teaching quality.
- A department that needs a lab will look high on space per FTE. That may be correct.

## Definitions and versions

Full definitions, formulas, owners and versions are in the [metric registry](../generated/metric-registry.md). Terms such as NIA and FTE are in the [business glossary](../generated/glossary.md). The measures used by this report are listed there under the space group.

## If a number surprises you

Check page 3 for that room. It shows the events behind the measure, plus a note of any events with no sensor cover. Most surprises are a filter left on, a room with no cover, or a double booking.
