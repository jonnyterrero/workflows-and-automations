# Thermal and Fluid Systems

## Conservation framework

Use a control volume when possible.

Mass:

\[
\frac{dm_{CV}}{dt}+\sum \dot m_{out}-\sum \dot m_{in}=0
\]

Steady incompressible continuity:

\[
Q=Av
\]

First law for a control volume:

\[
\dot Q-\dot W+
\sum_{in}\dot m\left(h+\frac{v^2}{2}+gz\right)
-
\sum_{out}\dot m\left(h+\frac{v^2}{2}+gz\right)=0
\]

## Heat transfer

Conduction:

\[
\dot Q=-kA\frac{dT}{dx}
\]

Convection:

\[
\dot Q=hA(T_s-T_\infty)
\]

Radiation:

\[
\dot Q=\epsilon\sigma A(T_s^4-T_{sur}^4)
\]

Use thermal resistance networks for lumped systems.

## Fluid-flow checks

Determine:
- Reynolds number
- laminar/turbulent regime
- pressure drop
- minor losses
- pump/fan operating point
- cavitation risk
- compressibility relevance

Bernoulli should include losses and machine work when required.

## Computational fluid work

Before CFD:
- estimate Reynolds number
- derive expected order of magnitude
- select domain and BCs
- justify turbulence model
- perform mesh independence
- check mass conservation
