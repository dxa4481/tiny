/*
 * TinyTapeout Silicon Art Project
 * 
 * This module is a minimal functional design for TinyTapeout.
 * The actual art (text/characters) is added via custom GDS layers.
 * 
 * The design passes inputs to outputs with a simple XOR pattern,
 * keeping the logic minimal so most of the silicon area is available for art.
 * 
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_silicon_art (
`ifdef USE_POWER_PINS
    inout  wire       VPWR,     // Power supply
    inout  wire       VGND,     // Ground
`endif
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // Always 1 when the design is powered
    input  wire       clk,      // Clock
    input  wire       rst_n     // Reset (active low)
);

    // Register to properly use clk and rst_n signals
    // This ensures these pins are connected in the synthesized design
    reg [7:0] latched_input;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            latched_input <= 8'b0;
        else if (ena)
            latched_input <= ui_in;
    end

    // Output: XOR pattern when enabled, latched value when disabled
    // This ensures ui_in, ena, clk, rst_n are all used
    assign uo_out = ena ? (ui_in ^ 8'hAA) : latched_input;
    
    // Bidirectional pins: pass through inputs to outputs
    // This ensures uio_in pins are connected
    assign uio_out = uio_in;
    assign uio_oe  = 8'b0;  // Configure all as inputs

endmodule
