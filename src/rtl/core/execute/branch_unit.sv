// branch_unit.sv - Branch Comparison Unit
// Part of the tri-mode SoC project
//
// Evaluates branch conditions for all RV64I branch instructions

module branch_unit
    import types_pkg::*;
    import rv64_pkg::*;
(
    input  xlen_t       rs1_data,       // Source register 1
    input  xlen_t       rs2_data,       // Source register 2
    input  logic [2:0]  branch_funct,   // Branch function code
    input  logic        is_branch,      // Is a branch instruction
    output logic        branch_taken    // Branch condition is true
);

    // Comparison results
    logic eq;           // rs1 == rs2
    logic lt_signed;    // rs1 < rs2 (signed)
    logic lt_unsigned;  // rs1 < rs2 (unsigned)

    assign eq = (rs1_data == rs2_data);
    assign lt_signed = $signed(rs1_data) < $signed(rs2_data);
    assign lt_unsigned = rs1_data < rs2_data;

    // Branch decision
    always_comb begin
        branch_taken = 1'b0;
        if (is_branch) begin
            case (branch_funct)
                BR_BEQ:  branch_taken = eq;
                BR_BNE:  branch_taken = !eq;
                BR_BLT:  branch_taken = lt_signed;
                BR_BGE:  branch_taken = !lt_signed;
                BR_BLTU: branch_taken = lt_unsigned;
                BR_BGEU: branch_taken = !lt_unsigned;
                default: branch_taken = 1'b0;
            endcase
        end
    end

endmodule
