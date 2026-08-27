# Power Electronics, Power Distribution, Batteries, and Charging

## Use for
- DC power distribution
- automotive electrical systems
- alternator-fed systems
- battery banks
- LTO/Li-ion/LiFePO4 systems
- DC-DC converters
- regulators
- inverters
- chargers
- high-current wiring
- fuse and conductor sizing

## Power-path model

For every design, draw:

```text
ENERGY SOURCE
    │
 protection
    │
 conductors/connectors
    │
 conversion/regulation
    │
 protection
    │
 LOAD
    │
 RETURN PATH
```

Explicitly model the return conductor/chassis resistance.

## Required calculations

Where relevant compute:
- continuous current
- peak current
- startup/inrush
- conductor voltage drop
- conductor power loss
- fuse coordination
- converter dissipation
- expected efficiency
- battery C-rate
- stored energy
- thermal rise
- recharge current and time
- source capacity

Basic relationships:

\[
P=VI
\]

\[
P_{loss}=I^2R
\]

\[
V_{drop}=IR
\]

\[
E=VQ
\]

For battery energy estimates:

\[
E_{Wh}\approx V_{nominal}\times Ah
\]

## High-current wiring

Do not judge cable only by gauge.

Check:
- conductor material
- length of supply and return path
- insulation temperature rating
- bundling
- ambient temperature
- termination quality
- connector resistance
- transient current
- allowable voltage drop

For a two-conductor run:

\[
R_{loop}=\rho\frac{L_{supply}+L_{return}}{A}
\]

## Fuse philosophy

A fuse primarily protects the **conductor and downstream system from fault energy**.

Fuse selection should consider:
- conductor ampacity
- expected continuous load
- allowable surge
- interrupt rating
- source fault capability
- placement near the energy source

## Battery-system safety

Always address:
- cell voltage limits
- current limits
- short-circuit energy
- balancing
- overcharge/overdischarge
- thermal monitoring
- precharge when large capacitance exists
- service disconnect
- enclosure and terminal protection

Do not recommend bypassing a protection system without explaining the resulting failure modes.
