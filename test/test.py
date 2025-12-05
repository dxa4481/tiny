# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_silicon_art(dut):
    """Test the silicon art design with outputs tied to ground."""
    
    dut._log.info("Starting silicon art test")

    # Create a clock
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

    # Test that outputs are grounded regardless of input (when ena=1)
    test_values = [0x00, 0xFF, 0xAA, 0x55, 0x12, 0x34]
    
    dut._log.info("Testing grounded outputs (ena=1)")
    for val in test_values:
        dut.ui_in.value = val
        await ClockCycles(dut.clk, 1)
        
        actual = int(dut.uo_out.value)
        
        dut._log.info(f"Input: 0x{val:02X}, Output: 0x{actual:02X} (expected 0x00)")
        assert actual == 0x00, f"Output should be grounded! Expected 0x00, got 0x{actual:02X}"

    # Test bidirectional outputs are also grounded
    dut._log.info("Testing bidirectional outputs grounded")
    dut.uio_in.value = 0x5A
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 0x00, f"uio_out should be grounded, got 0x{int(dut.uio_out.value):02X}"
    
    # Test that uio_oe is always 0 (configured as inputs)
    assert int(dut.uio_oe.value) == 0x00, "uio_oe should be 0x00"
    
    dut._log.info("All tests passed!")
