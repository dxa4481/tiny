/*
 * TinyTapeout Silicon Art Project
 * 
 * This module is a minimal functional design for TinyTapeout.
 * The actual art (text/characters) is added via custom GDS layers.
 * 
 * The design simply passes inputs to outputs with a simple pattern,
 * keeping the logic minimal so most of the silicon area is available for art.
 * 
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_silicon_art (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // Always 1 when the design is powered
    input  wire       clk,      // Clock
    input  wire       rst_n     // Reset (active low)
);

    // Simple pass-through with XOR pattern
    // This creates a minimal but valid design
    // The XOR with 8'hAA creates a nice checkerboard pattern when viewed
    assign uo_out = ui_in ^ 8'hAA;
    
    // Bidirectional pins configured as inputs (minimal logic)
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // List all unused inputs to prevent warnings
    wire _unused = &{ena, clk, rst_n, uio_in, 1'b0};

endmodule
