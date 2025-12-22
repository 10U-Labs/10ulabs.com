// imm_gen.sv - Immediate Generator for RV64I
// Part of the tri-mode SoC project
//
// Extracts and sign-extends immediates from all RV64I instruction formats:
// - I-type: 12-bit signed immediate
// - S-type: 12-bit signed immediate (split encoding)
// - B-type: 13-bit signed immediate (branch offset, LSB=0)
// - U-type: 20-bit upper immediate (shifted left 12)
// - J-type: 21-bit signed immediate (jump offset, LSB=0)

module imm_gen
    import types_pkg::*;
    import rv64_pkg::*;
(
    input  instr_t      instr,
    output xlen_t       imm_i,      // I-type immediate
    output xlen_t       imm_s,      // S-type immediate
    output xlen_t       imm_b,      // B-type immediate
    output xlen_t       imm_u,      // U-type immediate
    output xlen_t       imm_j       // J-type immediate
);

    // I-type: bits [31:20]
    // Sign-extend from bit 31
    assign imm_i = {{52{instr[31]}}, instr[31:20]};

    // S-type: bits [31:25] | [11:7]
    // Sign-extend from bit 31
    assign imm_s = {{52{instr[31]}}, instr[31:25], instr[11:7]};

    // B-type: bits [31] | [7] | [30:25] | [11:8] | 0
    // 13-bit offset with LSB always 0 (halfword aligned)
    // Sign-extend from bit 31
    assign imm_b = {{51{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};

    // U-type: bits [31:12] << 12
    // Upper 20 bits placed in bits [31:12], lower 12 bits are zero
    // Sign-extend from bit 31 to fill upper 32 bits
    assign imm_u = {{32{instr[31]}}, instr[31:12], 12'b0};

    // J-type: bits [31] | [19:12] | [20] | [30:21] | 0
    // 21-bit offset with LSB always 0 (halfword aligned)
    // Sign-extend from bit 31
    assign imm_j = {{43{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};

endmodule
