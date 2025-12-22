// pc_gen.sv - Program Counter Generation Logic
// Part of the tri-mode SoC project
//
// Computes next PC based on:
// - Sequential: PC + 4
// - Branch taken: PC + branch offset
// - JAL: PC + jump offset
// - JALR: rs1 + immediate (aligned to 2-byte boundary)

module pc_gen
    import types_pkg::*;
(
    input  pc_t         pc_current,     // Current PC
    input  xlen_t       rs1_data,       // rs1 value (for JALR)
    input  xlen_t       imm,            // Immediate (branch/jump offset)
    input  logic        branch_taken,   // Branch condition met
    input  logic        is_jal,         // JAL instruction
    input  logic        is_jalr,        // JALR instruction
    input  logic        stall,          // Pipeline stall
    output pc_t         pc_next,        // Next PC value
    output logic        pc_redirect     // PC is redirecting (not sequential)
);

    pc_t pc_plus_4;
    pc_t pc_branch;
    pc_t pc_jalr;

    // Sequential PC
    assign pc_plus_4 = pc_current + 64'd4;

    // Branch/JAL target: PC + offset
    assign pc_branch = pc_current + imm;

    // JALR target: (rs1 + imm) & ~1 (clear LSB for 2-byte alignment)
    assign pc_jalr = (rs1_data + imm) & ~64'd1;

    // Next PC selection
    always_comb begin
        if (stall) begin
            pc_next = pc_current;
            pc_redirect = 1'b0;
        end else if (is_jalr) begin
            pc_next = pc_jalr;
            pc_redirect = 1'b1;
        end else if (is_jal) begin
            pc_next = pc_branch;
            pc_redirect = 1'b1;
        end else if (branch_taken) begin
            pc_next = pc_branch;
            pc_redirect = 1'b1;
        end else begin
            pc_next = pc_plus_4;
            pc_redirect = 1'b0;
        end
    end

endmodule
