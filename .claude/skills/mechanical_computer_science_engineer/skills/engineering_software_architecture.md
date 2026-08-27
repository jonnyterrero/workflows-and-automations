# Engineering Software Architecture

## Goal

Build software that preserves engineering traceability and can be trusted.

## Architecture

Separate:
- domain physics
- numerical methods
- data access
- hardware I/O
- user interface
- reporting

Example:

```text
UI / API
   │
Application Layer
   │
Engineering Domain Model
   │
Numerical / Optimization Core
   │
Data + Hardware Adapters
```

## Code quality

For engineering calculations:
- functions should use explicit units or documented units
- constants should be named
- formulas should cite the physical model in comments/docstrings
- validation should catch impossible inputs
- outputs should include enough metadata to reproduce results

## Testing

Use:
- unit tests for formulas
- regression tests for known cases
- property tests where useful
- integration tests for hardware/software boundaries

## Data

Store:
- units
- timestamps
- calibration version
- sensor identity
- experiment configuration
- software version

A result that cannot be reproduced should not be treated as validated engineering evidence.
