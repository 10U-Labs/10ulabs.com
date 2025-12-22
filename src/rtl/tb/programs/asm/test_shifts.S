# test_shifts.S - Shift operations test
# Part of the tri-mode SoC project
#
# Tests: SLL, SRL, SRA, SLLI, SRLI, SRAI
# Pass: x31 = 1
# Fail: x31 = 0

.section .text
.globl _start

_start:
    # Initialize test status (fail by default)
    li      x31, 0

    # ===========================================
    # Test SLL (Shift Left Logical)
    # ===========================================
    li      x1, 1
    li      x2, 4
    sll     x3, x1, x2          # x3 = 1 << 4 = 16
    li      x4, 16
    bne     x3, x4, _fail

    # Test SLLI
    li      x1, 0x0F
    slli    x3, x1, 8           # x3 = 0x0F << 8 = 0x0F00
    li      x4, 0x0F00
    bne     x3, x4, _fail

    # ===========================================
    # Test SRL (Shift Right Logical)
    # ===========================================
    li      x1, 256
    li      x2, 4
    srl     x3, x1, x2          # x3 = 256 >> 4 = 16
    li      x4, 16
    bne     x3, x4, _fail

    # Test SRL with high bits (should zero-fill)
    li      x1, -1              # All 1s
    li      x2, 60
    srl     x3, x1, x2          # x3 = 0xFFFF...FFFF >> 60 = 0xF
    li      x4, 0xF
    bne     x3, x4, _fail

    # Test SRLI
    li      x1, 0xFF00
    srli    x3, x1, 8           # x3 = 0xFF00 >> 8 = 0xFF
    li      x4, 0xFF
    bne     x3, x4, _fail

    # ===========================================
    # Test SRA (Shift Right Arithmetic)
    # ===========================================
    # Positive number
    li      x1, 256
    li      x2, 4
    sra     x3, x1, x2          # x3 = 256 >> 4 = 16 (positive, same as SRL)
    li      x4, 16
    bne     x3, x4, _fail

    # Negative number (should sign-extend)
    li      x1, -256            # 0xFFFFFFFFFFFFFF00
    li      x2, 4
    sra     x3, x1, x2          # x3 = -256 >> 4 = -16
    li      x4, -16
    bne     x3, x4, _fail

    # Test SRAI with negative
    li      x1, -128
    srai    x3, x1, 2           # x3 = -128 >> 2 = -32
    li      x4, -32
    bne     x3, x4, _fail

    # ===========================================
    # Test 64-bit shifts
    # ===========================================
    li      x1, 1
    slli    x3, x1, 32          # x3 = 1 << 32 = 0x100000000
    li      x4, 0x100000000
    bne     x3, x4, _fail

    li      x1, 0x100000000
    srli    x3, x1, 32          # x3 = 0x100000000 >> 32 = 1
    li      x4, 1
    bne     x3, x4, _fail

    # ===========================================
    # All tests passed
    # ===========================================
    li      x31, 1              # Signal success

_done:
    j       _done               # Infinite loop

_fail:
    li      x31, 0              # Signal failure
    j       _done
