# Embedded Hardware + PCB Design

## Use for
- MCU boards
- sensor nodes
- Arduino-class systems
- custom PCBs
- interface boards
- power distribution boards
- embedded product design

## Architecture workflow

1. Define functional blocks.
2. Define power rails.
3. Define communication buses.
4. Define external interfaces.
5. Define clocks.
6. Define reset/boot behavior.
7. Define programming/debug path.
8. Define protection and test points.

Example:

```text
INPUT POWER
   │
[Protection]
   │
[Regulators] ── 5 V
   │            3.3 V
   │
[MCU] ── I2C ── Sensors
  │
  ├── SPI ── ADC
  ├── UART ── Debug
  └── GPIO ── Drivers
```

## Schematic review

Check:
- every IC power pin
- every required bypass capacitor
- pull-up/pull-down requirements
- unused pins
- reset circuit
- boot configuration
- oscillator network
- logic compatibility
- connector pinout
- input protection
- programming header

## Decoupling

Place high-frequency bypass capacitors physically near power pins.

Use bulk capacitance to support lower-frequency load transients.

Do not treat capacitance value alone as sufficient. Consider:
- ESR
- ESL
- package
- loop area
- placement

## PCB layout priorities

1. Return-current path
2. critical signal loop area
3. power distribution
4. clock/high-speed routing
5. analog isolation
6. thermal paths
7. mechanical constraints
8. manufacturability

## Layout review questions

- Where does the current return?
- Is the high di/dt loop minimized?
- Are switching nodes kept away from sensitive analog traces?
- Are crystal traces short?
- Are differential pairs routed as a pair?
- Are planes split in a way that forces return current around a gap?
- Are connectors protected from ESD?
- Are test points accessible?
