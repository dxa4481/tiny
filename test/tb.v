/*
 * Testbench for TinyTapeout Silicon Art Project
 *
 * This testbench wraps the tt_um_silicon_art module for simulation with cocotb.
 * 
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none
`timescale 1ns / 1ps

module tb ();

  // Dump the signals to a VCD file for waveform viewing
  initial begin
    $dumpfile("tb.vcd");
    $dumpvars(0, tb);
    #1;
  end

  // Wire up the inputs and outputs
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;

`ifdef GL_TEST
  // Gate-level test uses power pins
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif

  // Instantiate the module under test
  tt_um_silicon_art tt_um_silicon_art (
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif
      .ui_in  (ui_in),    // Dedicated inputs
      .uo_out (uo_out),   // Dedicated outputs
      .uio_in (uio_in),   // IOs: Input path
      .uio_out(uio_out),  // IOs: Output path
      .uio_oe (uio_oe),   // IOs: Enable path
      .ena    (ena),      // enable - active high
      .clk    (clk),      // clock
      .rst_n  (rst_n)     // active low reset
  );

endmodule
