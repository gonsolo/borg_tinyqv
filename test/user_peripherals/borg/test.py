import cocotb
from cocotb.clock import Clock
from tqv import TinyQV
import struct

# Helper to convert Python float to 32-bit uint bit pattern
def float_to_bits(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]

# Helper to convert 32-bit uint bit pattern back to Python float
def bits_to_float(b):
    return struct.unpack('<f', struct.pack('<I', b & 0xFFFFFFFF))[0]

PERIPHERAL_NUM = 39 

@cocotb.test()
async def test_borg_float_addition(dut):
    dut._log.info("Starting Borg Floating Point Addition Test")

    # 1. Start Clock (10MHz)
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # 2. Initialize TinyQV helper
    tqv = TinyQV(dut, PERIPHERAL_NUM)

    # 3. Reset
    await tqv.reset()

    # 4. Define Address Map
    ADDR_A      = 0
    ADDR_B      = 4
    ADDR_RESULT = 8

    # 5. Test Case: 1.25 + 2.5 = 3.75
    val_a = 1.25
    val_b = 2.5
    expected_sum = val_a + val_b

    bits_a = float_to_bits(val_a)
    bits_b = float_to_bits(val_b)

    dut._log.info(f"Writing A={val_a} ({hex(bits_a)}) and B={val_b} ({hex(bits_b)})")
    
    await tqv.write_word_reg(ADDR_A, bits_a)
    await tqv.write_word_reg(ADDR_B, bits_b)
    
    # 6. Read back result from Address 8
    dut._log.info(f"Reading back result from offset {ADDR_RESULT}...")
    actual_bits = await tqv.read_word_reg(ADDR_RESULT)
    actual_float = bits_to_float(actual_bits)
    
    dut._log.info(f"Read back bits: {hex(actual_bits)}")
    dut._log.info(f"Interpreted float: {actual_float}")

    # Use a small epsilon for comparison to handle potential rounding differences
    assert abs(actual_float - expected_sum) < 1e-6, \
        f"Float Addition failed! Expected {expected_sum}, got {actual_float}"

    # 7. Verify operand A is still readable
    read_bits_a = await tqv.read_word_reg(ADDR_A)
    assert read_bits_a == bits_a, f"Operand A corrupted! Got {hex(read_bits_a)}"

    dut._log.info("Borg Floating Point Addition Test Passed!")
