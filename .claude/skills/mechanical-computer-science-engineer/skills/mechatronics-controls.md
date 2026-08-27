# Mechatronics and Controls

## System decomposition

```text
REFERENCE → CONTROLLER → ACTUATOR → PLANT → SENSOR
                 ↑                    │
                 └──── FEEDBACK ──────┘
```

Model:
- actuator dynamics
- plant dynamics
- sensor dynamics
- latency
- saturation
- friction/deadband
- disturbances

## Controls workflow

1. Define controlled variable.
2. Define actuator.
3. Build plant model.
4. Determine stability.
5. Select control structure.
6. Tune controller.
7. Simulate.
8. Check saturation/noise.
9. Validate experimentally.

## PID

\[
u(t)=K_pe(t)+K_i\int e(t)dt+K_d\frac{de}{dt}
\]

Check:
- integral windup
- derivative noise
- sample rate
- actuator saturation

## Software implementation

Use explicit:
- sample period
- units
- state initialization
- saturation limits
- fault states
- watchdog behavior

For safety-critical motion, define a safe state independent of normal control logic.
