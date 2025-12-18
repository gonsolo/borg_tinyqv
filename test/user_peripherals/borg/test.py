import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
from tqv import TinyQV

PERIPHERAL_NUM = 39 # Ensure this matches your peripherals.v index

@cocotb.test()
async def test_borg_addition(dut):
    dut._log.info("Starting Borg Addition Test")

    # 1. Start Clock (100ns = 10MHz)
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    # 2. Initialize TinyQV helper
    tqv = TinyQV(dut, PERIPHERAL_NUM)

    # 3. Reset
    dut._log.info("Resetting system...")
    await tqv.reset()

    # 4. Define Address Map (Matching Chisel code)
    ADDR_A      = 0
    ADDR_B      = 4
    ADDR_RESULT = 8

    # 5. Perform Addition: A + B
    val_a = 0x42
    val_b = 0x01
    expected_sum = val_a + val_b

    dut._log.info(f"Writing A={hex(val_a)} to offset {ADDR_A}")
    await tqv.write_word_reg(ADDR_A, val_a)

    dut._log.info(f"Writing B={hex(val_b)} to offset {ADDR_B}")
    await tqv.write_word_reg(ADDR_B, val_b)
    
    # 6. Read back result from Address 8
    dut._log.info(f"Reading back result from offset {ADDR_RESULT}...")
    actual_val = await tqv.read_word_reg(ADDR_RESULT)
    
    dut._log.info(f"Read back sum: {hex(actual_val)}")

    assert actual_val == expected_sum, \
        f"Addition failed! Expected {hex(expected_sum)}, got {hex(actual_val)}"

    # 7. Optional: Verify operand A is still readable at offset 0
    val_read_a = await tqv.read_word_reg(ADDR_A)
    assert val_read_a == val_a, f"Operand A corrupted! Got {hex(val_read_a)}"

    dut._log.info("Borg Addition Test Passed!")
