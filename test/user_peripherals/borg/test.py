# SPDX-FileCopyrightText: © 2025 Andreas Wendleder
# SPDX-License-Identifier: CERN-OHL-S-2.0

import cocotb
from cocotb.clock import Clock
from tqv import TinyQV
import struct

def float_to_bits(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]

def bits_to_float(b):
    return struct.unpack('<f', struct.pack('<I', b & 0xFFFFFFFF))[0]

PERIPHERAL_NUM = 39

@cocotb.test()
async def test_borg_float_addition(dut):
    dut._log.info("Starting Borg Floating Point Addition Test")

    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())
    tqv = TinyQV(dut, PERIPHERAL_NUM)
    await tqv.reset()

    # Unified Address Map
    ADDR_A, ADDR_B, ADDR_RESULT = 0, 4, 8
    EPSILON = 1e-6

    val_a, val_b = 1.25, 2.5
    expected_sum = val_a + val_b

    await tqv.write_word_reg(ADDR_A, float_to_bits(val_a))
    await tqv.write_word_reg(ADDR_B, float_to_bits(val_b))
    
    actual_bits = await tqv.read_word_reg(ADDR_RESULT)
    actual_float = bits_to_float(actual_bits)
    
    dut._log.info(f"Initial Check: {val_a} + {val_b} = {actual_float}")
    assert abs(actual_float - expected_sum) < EPSILON, f"Failed: Got {actual_float}"

    read_bits_a = await tqv.read_word_reg(ADDR_A)
    assert read_bits_a == float_to_bits(val_a), "Operand A corrupted!"

    test_pairs = [
        (10.0, 20.0),
        (0.1, 0.2),
        (-5.5, 2.25),
        (100.0, 0.0),
        (1.23e-2, 4.56e-2)
    ]

    for a, b in test_pairs:
        await tqv.write_word_reg(ADDR_A, float_to_bits(a))
        await tqv.write_word_reg(ADDR_B, float_to_bits(b))
        res = bits_to_float(await tqv.read_word_reg(ADDR_RESULT))

        assert abs(res - (a + b)) < EPSILON, f"Iter failed: {a} + {b} = {res}"
        dut._log.info(f"Passed: {a} + {b} = {res}")

    dut._log.info("Borg Floating Point Addition Test Passed!")
