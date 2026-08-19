# Electrical + Hardware Engineer

A Claude skill pack for senior-level electrical and hardware engineering: circuit analysis, analog/mixed-signal design, power electronics, battery systems, embedded hardware, PCB design, digital logic/FPGA, signal integrity, grounding, EMC/EMI, lab debugging, and design review.

## Behavior

The agent works from first principles to implementation: establish requirements, derive the governing equations, size components, identify failure modes, verify margins, and propose a test plan. It does not stop at component suggestions.

## Structure

- `SKILL.md` — primary skill: workflow, calculation standard, design-review standard
- `skills/` — domain references loaded on demand (analog, power, PCB, digital/FPGA, SI/EMC, test, reliability)
- `templates/` — hardware design review checklist and electrical troubleshooting tree

## Install

Unzip into your Claude skills directory so the folder layout is `<skills-dir>/electrical-hardware-engineer/SKILL.md`.
