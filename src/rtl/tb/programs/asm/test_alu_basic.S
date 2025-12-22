# test_alu_basic.S - Basic ALU operations test
# Part of the tri-mode SoC project
#
# Tests: ADD, SUB, AND, OR, XOR, ADDI
# Pass: x31 = 1
# Fail: x31 = 0

.section .text
.globl _start

_start:
    # Initialize test status (fail by default)
    li      x31, 0

    # ===========================================
    # Test ADD
    # ===========================================
    li      x1, 5
    li      x2, 10
    add     x3, x1, x2          # x3 = 5 + 10 = 15
    li      x4, 15
    bne     x3, x4, _fail

    # Test ADD with negative
    li      x1, -5
    li      x2, 10
    add     x3, x1, x2          # x3 = -5 + 10 = 5
    li      x4, 5
    bne     x3, x4, _fail

    # ===========================================
    # Test SUB
    # ===========================================
    li      x1, 20
    li      x2, 7
    sub     x3, x1, x2          # x3 = 20 - 7 = 13
    li      x4, 13
    bne     x3, x4, _fail

    # Test SUB producing negative
    li      x1, 5
    li      x2, 10
    sub     x3, x1, x2          # x3 = 5 - 10 = -5
    li      x4, -5
    bne     x3, x4, _fail

    # ===========================================
    # Test AND
    # ===========================================
    li      x1, 0xFF00FF00
    li      x2, 0x0FF00FF0
    and     x3, x1, x2          # x3 = 0x0F000F00
    li      x4, 0x0F000F00
    bne     x3, x4, _fail

    # ===========================================
    # Test OR
    # ===========================================
    li      x1, 0xFF00FF00
    li      x2, 0x00FF00FF
    or      x3, x1, x2          # x3 = 0xFFFFFFFF
    li      x4, 0xFFFFFFFF
    bne     x3, x4, _fail

    # ===========================================
    # Test XOR
    # ===========================================
    li      x1, 0xFF00FF00
    li      x2, 0xFFFF0000
    xor     x3, x1, x2          # x3 = 0x00FFFF00
    li      x4, 0x00FFFF00
    bne     x3, x4, _fail

    # ===========================================
    # Test ADDI
    # ===========================================
    li      x1, 100
    addi    x3, x1, 50          # x3 = 100 + 50 = 150
    li      x4, 150
    bne     x3, x4, _fail

    # Test ADDI with negative immediate
    li      x1, 100
    addi    x3, x1, -30         # x3 = 100 - 30 = 70
    li      x4, 70
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
