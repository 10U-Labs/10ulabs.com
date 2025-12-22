# test_branches.S - Branch instructions test
# Part of the tri-mode SoC project
#
# Tests: BEQ, BNE, BLT, BGE, BLTU, BGEU
# Pass: x31 = 1
# Fail: x31 = 0

.section .text
.globl _start

_start:
    # Initialize test status (fail by default)
    li      x31, 0
    li      x10, 0              # Test counter

    # ===========================================
    # Test BEQ (Branch if Equal)
    # ===========================================
    li      x1, 42
    li      x2, 42
    beq     x1, x2, beq_pass
    j       _fail
beq_pass:
    addi    x10, x10, 1         # Test 1 passed

    # BEQ should not branch when not equal
    li      x1, 10
    li      x2, 20
    beq     x1, x2, _fail
    addi    x10, x10, 1         # Test 2 passed

    # ===========================================
    # Test BNE (Branch if Not Equal)
    # ===========================================
    li      x1, 10
    li      x2, 20
    bne     x1, x2, bne_pass
    j       _fail
bne_pass:
    addi    x10, x10, 1         # Test 3 passed

    # BNE should not branch when equal
    li      x1, 42
    li      x2, 42
    bne     x1, x2, _fail
    addi    x10, x10, 1         # Test 4 passed

    # ===========================================
    # Test BLT (Branch if Less Than - signed)
    # ===========================================
    li      x1, -10
    li      x2, 10
    blt     x1, x2, blt_pass    # -10 < 10 (signed)
    j       _fail
blt_pass:
    addi    x10, x10, 1         # Test 5 passed

    # BLT should not branch when >=
    li      x1, 10
    li      x2, 10
    blt     x1, x2, _fail
    addi    x10, x10, 1         # Test 6 passed

    # ===========================================
    # Test BGE (Branch if Greater or Equal - signed)
    # ===========================================
    li      x1, 10
    li      x2, -10
    bge     x1, x2, bge_pass    # 10 >= -10 (signed)
    j       _fail
bge_pass:
    addi    x10, x10, 1         # Test 7 passed

    # Test BGE with equal values
    li      x1, 42
    li      x2, 42
    bge     x1, x2, bge_eq_pass
    j       _fail
bge_eq_pass:
    addi    x10, x10, 1         # Test 8 passed

    # ===========================================
    # Test BLTU (Branch if Less Than - unsigned)
    # ===========================================
    li      x1, 10
    li      x2, -1              # -1 = 0xFFFFFFFFFFFFFFFF (very large unsigned)
    bltu    x1, x2, bltu_pass   # 10 < 0xFFFF...FFFF (unsigned)
    j       _fail
bltu_pass:
    addi    x10, x10, 1         # Test 9 passed

    # ===========================================
    # Test BGEU (Branch if Greater or Equal - unsigned)
    # ===========================================
    li      x1, -1              # 0xFFFFFFFFFFFFFFFF
    li      x2, 10
    bgeu    x1, x2, bgeu_pass   # 0xFFFF...FFFF >= 10 (unsigned)
    j       _fail
bgeu_pass:
    addi    x10, x10, 1         # Test 10 passed

    # ===========================================
    # All tests passed
    # ===========================================
    li      x4, 10              # Expected test count
    bne     x10, x4, _fail      # Verify all tests ran
    li      x31, 1              # Signal success

_done:
    j       _done               # Infinite loop

_fail:
    li      x31, 0              # Signal failure
    j       _done
