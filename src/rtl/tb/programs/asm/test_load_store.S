# test_load_store.S - Load and Store instructions test
# Part of the tri-mode SoC project
#
# Tests: LB, LH, LW, LD, LBU, LHU, LWU, SB, SH, SW, SD
# Pass: x31 = 1
# Fail: x31 = 0
#
# Note: Data memory starts at 0x80010000 in our memory map

.section .text
.globl _start

_start:
    # Initialize test status (fail by default)
    li      x31, 0

    # Base address for data memory
    li      x20, 0x80010000

    # ===========================================
    # Test SD/LD (Store/Load Doubleword)
    # ===========================================
    li      x1, 0xDEADBEEFCAFEBABE
    sd      x1, 0(x20)          # Store doubleword
    ld      x2, 0(x20)          # Load doubleword
    bne     x1, x2, _fail

    # ===========================================
    # Test SW/LW (Store/Load Word - sign extended)
    # ===========================================
    li      x1, 0x12345678
    sw      x1, 8(x20)          # Store word at offset 8
    lw      x2, 8(x20)          # Load word (sign-extended)
    li      x3, 0x12345678      # Expected (positive, no sign extension)
    bne     x2, x3, _fail

    # Test LW with negative value (sign extension)
    li      x1, 0xFFFFFFFF80000000  # -2147483648 as 64-bit
    sw      x1, 16(x20)         # Store lower 32 bits (0x80000000)
    lw      x2, 16(x20)         # Load word (sign-extended)
    li      x3, 0xFFFFFFFF80000000  # Expected: sign-extended to 64-bit
    bne     x2, x3, _fail

    # ===========================================
    # Test LWU (Load Word Unsigned - zero extended)
    # ===========================================
    lwu     x2, 16(x20)         # Load same value but unsigned
    li      x3, 0x80000000      # Expected: zero-extended
    bne     x2, x3, _fail

    # ===========================================
    # Test SH/LH (Store/Load Halfword - sign extended)
    # ===========================================
    li      x1, 0x1234
    sh      x1, 24(x20)         # Store halfword
    lh      x2, 24(x20)         # Load halfword (sign-extended)
    li      x3, 0x1234
    bne     x2, x3, _fail

    # Test LH with negative value
    li      x1, 0x8000          # -32768 as halfword
    sh      x1, 32(x20)
    lh      x2, 32(x20)         # Load halfword (sign-extended)
    li      x3, 0xFFFFFFFFFFFF8000  # Expected: sign-extended
    bne     x2, x3, _fail

    # ===========================================
    # Test LHU (Load Halfword Unsigned)
    # ===========================================
    lhu     x2, 32(x20)         # Load same value unsigned
    li      x3, 0x8000          # Expected: zero-extended
    bne     x2, x3, _fail

    # ===========================================
    # Test SB/LB (Store/Load Byte - sign extended)
    # ===========================================
    li      x1, 0x42
    sb      x1, 40(x20)         # Store byte
    lb      x2, 40(x20)         # Load byte (sign-extended)
    li      x3, 0x42
    bne     x2, x3, _fail

    # Test LB with negative value
    li      x1, 0x80            # -128 as signed byte
    sb      x1, 48(x20)
    lb      x2, 48(x20)         # Load byte (sign-extended)
    li      x3, 0xFFFFFFFFFFFFFF80  # Expected: sign-extended
    bne     x2, x3, _fail

    # ===========================================
    # Test LBU (Load Byte Unsigned)
    # ===========================================
    lbu     x2, 48(x20)         # Load same value unsigned
    li      x3, 0x80            # Expected: zero-extended
    bne     x2, x3, _fail

    # ===========================================
    # All tests passed
    # ===========================================
    li      x31, 1              # Signal success

_done:
    j       _done               # Infinite loop

_fail:
    li      x31, 0              # Signal failure
    j       _done
