# Circuit Analysis + Analog / Mixed-Signal Design

## Use for
- resistor networks
- op-amp circuits
- transistor biasing
- filters
- sensor front ends
- ADC/DAC interfaces
- amplifiers
- oscillators
- analog signal conditioning

## Analysis sequence

1. Identify DC operating point.
2. Determine small-signal behavior if applicable.
3. Calculate input/output impedance.
4. Calculate gain or transfer function.
5. Determine bandwidth.
6. Calculate noise/error sources.
7. Check output swing and current limits.
8. Verify stability.
9. Check tolerance sensitivity.

## Op-amp checklist

Verify:
- input common-mode range
- output swing
- gain-bandwidth product
- slew rate
- input bias current
- offset voltage
- noise density
- capacitive-load stability
- supply range
- rail sequencing if relevant

Do not assume an op amp is ideal unless the problem explicitly calls for ideal analysis.

## ADC front-end checklist

Quantify:
- full-scale range
- LSB size
- source impedance
- acquisition time
- anti-alias filtering
- reference accuracy
- quantization noise
- sensor offset/gain error
- common-mode constraints

For an N-bit ideal ADC:

\[
LSB = \frac{V_{FS}}{2^N}
\]

Approximate ideal quantization SNR for a full-scale sine:

\[
SNR_{ideal} \approx 6.02N + 1.76\text{ dB}
\]

## Filter design

State:
- topology
- order
- passband
- cutoff
- stopband requirement
- expected phase behavior

For a first-order RC low-pass:

\[
f_c=\frac{1}{2\pi RC}
\]

Check whether the source and load impedances alter the nominal pole.
