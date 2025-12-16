# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.types import LogicArray
import struct
import math

from tqv import TinyQV

PERIPHERAL_NUM = 39

# --- UTILITY FUNCTIONS ---

def float_to_ieee_bits(f: float) -> int:
    """Converts a Python float (64-bit) to its 32-bit IEEE 754 raw integer representation."""
    # Use 'f' for 32-bit float, '<' for little-endian byte order
    return struct.unpack('<I', struct.pack('<f', f))[0]

def ieee_bits_to_float(i: int) -> float:
    """Converts a 32-bit IEEE 754 raw integer representation to a Python float (64-bit)."""
    # Use 'I' for unsigned 32-bit integer, '<' for little-endian byte order
    return struct.unpack('<f', struct.pack('<I', i))[0]

# --- COCOTB TEST ---

@cocotb.test()
async def test_floating_point_adder(dut): # Renamed function
    dut._log.info("Start test_floating_point_adder")

    # Set up the clock and reset
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut, PERIPHERAL_NUM)
    await tqv.reset()
    
    # Define a consistent wait time for pipeline completion
    COMPUTATION_WAIT_CYCLES = 1

    dut._log.info("Testing simple addition: A + B")

    # 1. Define Floating Point Operands (Matching your Chisel test)
    OPERAND_A_FLOAT = 123.5
    OPERAND_B_FLOAT = 456.75
    
    # 2. Calculate the expected result using Python's math
    EXPECTED_SUM_FLOAT = OPERAND_A_FLOAT + OPERAND_B_FLOAT # Should be 580.25
    
    # 3. Convert the operands to the 32-bit integer representation for the hardware
    OPERAND_A_BITS = float_to_ieee_bits(OPERAND_A_FLOAT)
    OPERAND_B_BITS = float_to_ieee_bits(OPERAND_B_FLOAT)
    
    # 4. Convert the expected Python result to the 32-bit integer representation
    # NOTE: This ensures the expected value reflects any precision loss from FP32
    EXPECTED_SUM_BITS = float_to_ieee_bits(EXPECTED_SUM_FLOAT)
    
    # Log the values used
    dut._log.info(f"A_float = {OPERAND_A_FLOAT}, B_float = {OPERAND_B_FLOAT}")
    dut._log.info(f"Expected Sum (Python) = {EXPECTED_SUM_FLOAT}")
    dut._log.info(f"A_bits = 0x{OPERAND_A_BITS:08x}, B_bits = 0x{OPERAND_B_BITS:08x}")
    dut._log.info(f"Expected Sum (FP32 bits) = 0x{EXPECTED_SUM_BITS:08x}")

    # --- Write Operands to Hardware Registers (Addresses 0 and 4) ---

    await tqv.write_word_reg(0, OPERAND_A_BITS)
    await tqv.write_word_reg(4, OPERAND_B_BITS)

    # Wait for computation (using the safe, long wait time)
    await ClockCycles(dut.clk, COMPUTATION_WAIT_CYCLES)

    # --- Read Result from Hardware Register (Address 8) ---
    
    ACTUAL_SUM_BITS = await tqv.read_word_reg(8)

    # Log the actual result from the hardware
    dut._log.info(f"Actual Sum Read (FP32 bits): 0x{ACTUAL_SUM_BITS:08x}")
    
    ACTUAL_SUM_FLOAT = ieee_bits_to_float(ACTUAL_SUM_BITS)
    dut._log.info(f"Actual Sum Read (Float) for precision test: {ACTUAL_SUM_FLOAT}") #

    # Check the result bit-for-bit against the expected 32-bit pattern
    assert ACTUAL_SUM_BITS == EXPECTED_SUM_BITS, \
        f"Addition failed: Expected bit pattern 0x{EXPECTED_SUM_BITS:08x}, " \
        f"got 0x{ACTUAL_SUM_BITS:08x}"

    dut._log.info("Floating Point Adder Test Passed!")
    
    # --- Test Case 2: Special Values (Adding a large and a small number) ---
    dut._log.info("Testing precision: 1.0 + 1.0e-10")

    A_LARGE_FLOAT = 1.0
    B_SMALL_FLOAT = 1.0e-10 # This value is likely lost in FP32 addition (result is 1.0)
    EXPECTED_FLOAT = 1.0 # The true FP32 sum of 1.0 and 1.0e-10 is 1.0
    
    A_LARGE_BITS = float_to_ieee_bits(A_LARGE_FLOAT)
    B_SMALL_BITS = float_to_ieee_bits(B_SMALL_FLOAT)
    EXPECTED_BITS = float_to_ieee_bits(EXPECTED_FLOAT) # Expected FP32 bit pattern for 1.0

    await tqv.write_word_reg(0, A_LARGE_BITS)
    await tqv.write_word_reg(4, B_SMALL_BITS)
    await ClockCycles(dut.clk, COMPUTATION_WAIT_CYCLES)
    ACTUAL_BITS = await tqv.read_word_reg(8)

    assert ACTUAL_BITS == EXPECTED_BITS, "Precision test failed (large + small number)"
    dut._log.info("Precision Test Passed!")
