# P09 — Inspection frequencies (illustrative, not legal duties)

> **Do not use these frequencies for real compliance.** They are seeded
> configuration in `campus_synth`. Before any real deployment, the human
> must verify each against current legal duties and guidance.

| Inspection type | Frequency (months) | Applies to | Typical legal reference (verify independently) |
|---|---|---|---|
| INSP-LEG (Legionella control check) | 3 | all buildings | HSE L8 ACOP, HSG274 |
| INSP-FIRE (Fire alarm servicing) | 6 | Fire Alarm Panel | BS 5839-1, Fire Safety Order 2005 |
| INSP-LIFT (Lift thorough examination) | 6 | Lift | LOLER 1998, PUWER 1998 |
| INSP-GAS (Gas safety check) | 12 | Boiler | Gas Safety (Installation & Use) Regs 1998 |
| INSP-ELEC (Electrical condition report) | 60 | all buildings | BS 7671, Electricity at Work Regs 1989 |

**Sources to verify (human action):**
- HSE L8 ACOP / HSG274 (legionella)
- BS 5839-1 (fire detection & alarm)
- LOLER 1998 / PUWER 1998 (lifting equipment)
- Gas Safety (Installation & Use) Regulations 1998
- BS 7671 (IET Wiring Regulations) / Electricity at Work Regulations 1989

**Action required:** The human must read the current versions of the above,
confirm or update the frequencies in the config, and document the decision.
This file is a reminder; it does not constitute legal advice.