# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_silicon_art(dut):
    """Test the silicon art design with outputs tied to ground."""
    
    dut._log.info("Starting silicon art test")

    # Create a clock (not really needed for combinational logic but required by TT)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # Test that outputs are always grounded regardless of input
    test_values = [0x00, 0xFF, 0xAA, 0x55, 0x12, 0x34]
    
    for val in test_values:
        dut.ui_in.value = val
        await ClockCycles(dut.clk, 1)
        
        # All outputs should be grounded (0x00)
        actual = int(dut.uo_out.value)
        
        dut._log.info(f"Input: 0x{val:02X}, Output: 0x{actual:02X} (expected 0x00)")
        assert actual == 0x00, f"Output should be grounded! Expected 0x00, got 0x{actual:02X}"
    
    dut._log.info("All tests passed!")
