# CAD, FEA, and Simulation

## CAD

A CAD model should communicate:
- functional geometry
- datums
- interfaces
- tolerances
- material
- manufacturing intent

Avoid unnecessary geometric detail during early analysis.

## FEA workflow

1. Define the engineering question.
2. Simplify geometry.
3. Choose element type.
4. Define material model.
5. Define contacts.
6. Apply loads.
7. Apply constraints.
8. Mesh.
9. Solve.
10. Check convergence.
11. Compare with hand calculation.
12. Interpret stress away from singularities.

## FEA sanity checks

- reaction forces balance applied loads
- deformation direction is physically sensible
- symmetry is preserved where expected
- mesh refinement changes results acceptably
- peak stresses at singular corners are not blindly treated as physical
- units are consistent

## Automation

Use scripting to automate:
- parameter sweeps
- geometry generation
- mesh studies
- optimization
- post-processing
- report generation

Keep model inputs explicit and version-controlled.
