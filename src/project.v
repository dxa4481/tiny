/*
 * TinyTapeout Silicon Art Project
 * 
 * This module is a minimal functional design for TinyTapeout.
 * The actual art (text/characters) is added via custom GDS layers.
 * 
 * All outputs are tied to ground (0) for minimal logic, while maintaining
 * proper connections to all input pins to satisfy synthesis requirements.
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

    // Register to ensure clk and rst_n pins are connected in synthesis
    reg [7:0] latched_input;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            latched_input <= 8'b0;
        else if (ena)
            latched_input <= ui_in;
    end

    // Outputs are grounded (0) during normal operation (ena=1)
    // The conditional ensures ui_in/latched_input stay connected in synthesis
    // Since ena is always 1 when powered, outputs are always 0
    assign uo_out = ena ? 8'b0 : latched_input;
    
    // Bidirectional outputs grounded, but uio_in stays connected via conditional
    assign uio_out = ena ? 8'b0 : uio_in;
    assign uio_oe  = 8'b0;  // Configure all as inputs

endmodule
