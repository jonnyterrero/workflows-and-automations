# Digital Hardware, FPGA, and Interfaces

## Use for
- combinational/sequential logic
- FPGA/CPLD
- Verilog/SystemVerilog/VHDL
- timing analysis
- memory interfaces
- SPI/I2C/UART/CAN
- logic-level translation
- high-speed digital design

## Digital design workflow

1. Write behavioral requirement.
2. Define clock domains.
3. Define reset behavior.
4. Identify latency and throughput.
5. Define interface timing.
6. Implement logic.
7. Simulate.
8. Perform static timing analysis.
9. Verify on hardware.

## Timing

For synchronous paths, reason using:

\[
T_{clk} \ge t_{clk\rightarrow q}+t_{comb}+t_{setup}+t_{skew}+margin
\]

Also inspect hold constraints.

## Clock-domain crossings

Never pass arbitrary multi-bit buses between unrelated clock domains without a defined CDC strategy.

Common techniques:
- two-flop synchronizer for single control bits
- pulse synchronizer
- handshake
- asynchronous FIFO
- Gray-code pointers/counters

## Interface analysis

For every bus identify:
- voltage levels
- direction
- topology
- pull-up/termination requirements
- clock/data rate
- maximum cable/trace length
- bus capacitance
- startup states
- fault behavior

## HDL standard

When producing HDL:
- use synthesizable constructs unless simulation-only code is requested
- avoid inferred latches unless intentional
- use explicit reset strategy
- separate combinational and sequential logic cleanly
- provide a minimal testbench when useful
