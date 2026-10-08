# P16 Power BI README — question → insight → decision (synthetic campus)

- **Which meters are burning money outside hours?** → B007-E01's overnight mean
  sits at 60% of its peak and rises over the series (planted fault); it carries
  £7,817/yr of the £9,800 total attributed → *survey the overnight HVAC schedule
  on B007 first; it is the single biggest item on the list.*
- **What are the most common fault types?** → across 18 synthetic meters the
  spike and step-change labels dominate, and 6 of the top 10 findings are spikes
  (`fct_finding` exploded from the scorecard) → *spikes are cheap to fix and
  frequent: check for stuck plant rather than chasing baseloads first.*
- **Which meters are data problems rather than energy problems?** → the
  flat-line and missing-data labels carry £0 savings by design, because a stuck
  meter's real use cannot be estimated → *fix the meter and its comms before
  budgeting any saving against it.*
- **Where does the money sit?** → the top 3 meters carry the large majority of
  attributed annual cost (`Top 3 Cost Concentration`) → *a small review team can
  work this list top-down; there is no need to re-inspect all 18 meters.*

Not in this report: BDG2. Those are public, USD-priced, unlabelled review
candidates with no accuracy claim, and putting them next to synthetic £ figures
would invite a comparison that the data does not support. They live in
`outputs/bdg2/` as HTML evidence pages plus `review.json`.