# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_silicon_art(dut):
    """Test the silicon art design with XOR pattern output."""
    
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

    # Test XOR pattern: output = input XOR 0xAA when enabled
    test_cases = [
        (0x00, 0xAA),  # 0x00 XOR 0xAA = 0xAA
        (0xFF, 0x55),  # 0xFF XOR 0xAA = 0x55
        (0xAA, 0x00),  # 0xAA XOR 0xAA = 0x00
        (0x55, 0xFF),  # 0x55 XOR 0xAA = 0xFF
        (0x12, 0xB8),  # 0x12 XOR 0xAA = 0xB8
        (0x34, 0x9E),  # 0x34 XOR 0xAA = 0x9E
    ]
    
    dut._log.info("Testing XOR pattern (ena=1)")
    for input_val, expected in test_cases:
        dut.ui_in.value = input_val
        await ClockCycles(dut.clk, 1)
        
        actual = int(dut.uo_out.value)
        
        dut._log.info(f"Input: 0x{input_val:02X}, Output: 0x{actual:02X} (expected 0x{expected:02X})")
        assert actual == expected, f"XOR pattern failed! Expected 0x{expected:02X}, got 0x{actual:02X}"

    # Test bidirectional pass-through
    dut._log.info("Testing bidirectional pass-through")
    dut.uio_in.value = 0x5A
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 0x5A, "Bidirectional pass-through failed"
    
    # Test that uio_oe is always 0 (configured as inputs)
    assert int(dut.uio_oe.value) == 0x00, "uio_oe should be 0x00"
    
    dut._log.info("All tests passed!")
