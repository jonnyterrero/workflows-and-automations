# Signal Integrity, Grounding, EMI, and EMC

## Core principle

A signal is not only a voltage on one conductor. It is a **current loop** with a forward path and a return path.

Noise problems should be analyzed by identifying:
- source
- coupling path
- victim

## Grounding diagnosis

Possible causes:
- shared impedance
- ground-loop current
- chassis potential difference
- poor termination
- shield current
- conducted alternator/switching ripple
- capacitive coupling
- inductive coupling
- radiated coupling

For a ground conductor:

\[
V_{ground\ shift}=I_{return}R_{ground}
\]

Even milliohms can matter at high current.

## Troubleshooting order

1. Confirm the noise source.
2. Determine whether noise is conducted or radiated.
3. Measure voltage difference between supposed ground points under load.
4. Inspect return-current routing.
5. Disconnect subsystems to isolate coupling paths.
6. Test temporary low-impedance bonding.
7. Verify shield and RCA/reference routing.
8. Only then add filters if needed.

## High-speed signal integrity

Estimate whether transmission-line behavior matters using edge rate, not merely clock frequency.

Inspect:
- source/load impedance
- trace impedance
- reflections
- overshoot/undershoot
- ringing
- termination
- via stubs
- plane discontinuities
- crosstalk

## EMC mitigation hierarchy

Prefer:
1. reduce noise at source
2. minimize coupling path
3. harden victim
4. add shielding/filtering where justified

Avoid using ferrites or capacitors without identifying the relevant frequency range and current path.
