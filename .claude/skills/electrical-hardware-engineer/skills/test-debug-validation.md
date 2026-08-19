# Lab Test, Debugging, and Validation

## Objective

Find faults efficiently and prove that a repaired/design solution meets requirements.

## Debugging method

Use binary partitioning of the system whenever possible.

For each measurement define:
- hypothesis
- expected result if hypothesis is true
- expected result if false
- next action

## Measurement discipline

Before trusting a measurement, verify:
- meter/scope bandwidth
- probe reference
- probe loading
- correct AC/DC coupling
- RMS vs average interpretation
- current-probe orientation
- instrument ground safety
- sampling rate

## Oscilloscope use

When relevant examine:
- DC level
- ripple
- startup transient
- overshoot
- ringing
- switching waveform
- timing relationship
- noise spectrum

Use short probe ground connections for high-frequency measurements.

## Design verification matrix

| Requirement | Test | Instrument | Expected | Pass/Fail |
|---|---|---|---|---|

Every critical requirement should map to at least one test.

## Troubleshooting answer format

1. Most likely mechanisms
2. Why each mechanism fits the symptoms
3. Tests in priority order
4. Expected readings
5. Corrective action for each possible result
6. Safety constraints
