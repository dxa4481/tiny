<!---
This file is used to generate your project datasheet. Please fill in the information below and delete any unused sections.
-->

## How it works

This is a **Silicon Art** project for TinyTapeout. The primary goal is to create text and graphics that will be visible under a microscope when the chip is fabricated.

The design includes:
1. A minimal functional Verilog design (XOR pass-through)
2. Custom text/graphics added to metal layers via GDS post-processing
3. The text "Hello World!" rendered in silicon

The functional logic is minimal - it simply XORs the 8-bit input with 0xAA (10101010 in binary), creating a checkerboard pattern. This keeps the standard cell usage low, leaving more silicon area available for the art.

## How to test

1. Apply any 8-bit input pattern to `ui_in[7:0]`
2. The output `uo_out[7:0]` will be the input XOR'd with 0xAA

For example:
- Input: 0x00 → Output: 0xAA
- Input: 0xFF → Output: 0x55
- Input: 0xAA → Output: 0x00

## External hardware

No external hardware required. This is primarily an art project.

To view the silicon art:
- Use an optical microscope with at least 50x magnification
- A metallurgical/reflected light microscope works best
- The text is visible in the metal layers of the fabricated chip
