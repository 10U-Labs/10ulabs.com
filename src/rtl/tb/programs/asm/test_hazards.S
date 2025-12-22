# test_hazards.S - Data hazard and forwarding test
# Part of the tri-mode SoC project
#
# Tests:
# - RAW hazards with forwarding (EX->EX, MEM->EX)
# - Load-use hazards (require stall)
# Pass: x31 = 1
# Fail: x31 = 0

.section .text
.globl _start

_start:
    # Initialize test status (fail by default)
    li      x31, 0

    # Base address for data memory
    li      x20, 0x80010000

    # ===========================================
    # Test 1: Simple RAW hazard (EX->EX forwarding)
    # ===========================================
    li      x1, 10
    add     x2, x1, x1          # x2 = 20 (uses x1 from previous)
    add     x3, x2, x2          # x3 = 40 (uses x2 from previous)
    li      x4, 40
    bne     x3, x4, _fail

    # ===========================================
    # Test 2: Two-cycle RAW (MEM->EX forwarding)
    # ===========================================
    li      x1, 5
    nop                         # One cycle gap
    add     x2, x1, x1          # x2 = 10 (uses x1 from two cycles ago)
    li      x3, 10
    bne     x2, x3, _fail

    # ===========================================
    # Test 3: Chain of dependent instructions
    # ===========================================
    li      x1, 1
    add     x2, x1, x1          # x2 = 2
    add     x3, x2, x2          # x3 = 4
    add     x4, x3, x3          # x4 = 8
    add     x5, x4, x4          # x5 = 16
    li      x6, 16
    bne     x5, x6, _fail

    # ===========================================
    # Test 4: Load-use hazard (requires stall)
    # ===========================================
    li      x1, 42
    sd      x1, 0(x20)          # Store 42
    ld      x2, 0(x20)          # Load 42
    add     x3, x2, x2          # x3 = 84 (uses loaded value - needs stall)
    li      x4, 84
    bne     x3, x4, _fail

    # ===========================================
    # Test 5: Load followed by dependent store
    # ===========================================
    li      x1, 100
    sd      x1, 8(x20)          # Store 100 at offset 8
    ld      x2, 8(x20)          # Load it back
    addi    x2, x2, 1           # Increment (load-use hazard)
    sd      x2, 16(x20)         # Store 101 at offset 16
    ld      x3, 16(x20)         # Load it back
    li      x4, 101
    bne     x3, x4, _fail

    # ===========================================
    # Test 6: Multiple hazards in sequence
    # ===========================================
    li      x1, 1
    li      x2, 2
    add     x3, x1, x2          # x3 = 3 (hazards on x1 and x2)
    add     x4, x3, x3          # x4 = 6 (hazard on x3)
    sd      x4, 24(x20)         # Store 6
    ld      x5, 24(x20)         # Load 6
    add     x6, x5, x5          # x6 = 12 (load-use hazard)
    li      x7, 12
    bne     x6, x7, _fail

    # ===========================================
    # Test 7: x0 should not cause false hazards
    # ===========================================
    add     x0, x0, x0          # Write to x0 (should be ignored)
    li      x1, 0
    beq     x1, x0, x0_pass     # x0 should still be 0
    j       _fail
x0_pass:

    # ===========================================
    # All tests passed
    # ===========================================
    li      x31, 1              # Signal success

_done:
    j       _done               # Infinite loop

_fail:
    li      x31, 0              # Signal failure
    j       _done
