// execute_stage.sv - Execute Stage
// Part of the tri-mode SoC project
//
// Responsibilities:
// - Execute ALU operations
// - Evaluate branch conditions
// - Compute branch/jump targets
// - Apply forwarding

module execute_stage
    import types_pkg::*;
    import rv64_pkg::*;
    import pipeline_pkg::*;
(
    // Input from ID/EX pipeline register
    input  id_ex_t      id_ex_in,

    // Forwarding inputs
    input  fwd_sel_t    fwd_rs1,
    input  fwd_sel_t    fwd_rs2,
    input  xlen_t       fwd_ex_mem_data,    // Data from EX/MEM stage
    input  xlen_t       fwd_mem_wb_data,    // Data from MEM/WB stage

    // Output to EX/MEM pipeline register
    output ex_mem_t     ex_mem_out
);

    // Forwarded operands
    xlen_t rs1_fwd, rs2_fwd;

    // ALU operands
    xlen_t alu_a, alu_b;

    // ALU outputs
    xlen_t alu_result;
    logic  alu_zero, alu_neg, alu_ovf;

    // Branch unit output
    logic  branch_taken;

    // Branch/Jump target
    pc_t   branch_target;

    // Forwarding mux for rs1
    always_comb begin
        case (fwd_rs1)
            FWD_EX_MEM: rs1_fwd = fwd_ex_mem_data;
            FWD_MEM_WB: rs1_fwd = fwd_mem_wb_data;
            default:    rs1_fwd = id_ex_in.rs1_data;
        endcase
    end

    // Forwarding mux for rs2
    always_comb begin
        case (fwd_rs2)
            FWD_EX_MEM: rs2_fwd = fwd_ex_mem_data;
            FWD_MEM_WB: rs2_fwd = fwd_mem_wb_data;
            default:    rs2_fwd = id_ex_in.rs2_data;
        endcase
    end

    // ALU operand A: rs1 or PC (for AUIPC)
    always_comb begin
        if (id_ex_in.alu_op == ALU_ADD && id_ex_in.alu_src &&
            id_ex_in.imm[31:12] != '0 && !id_ex_in.is_load && !id_ex_in.is_store &&
            !id_ex_in.is_jalr) begin
            // AUIPC: PC + upper immediate
            alu_a = id_ex_in.pc;
        end else begin
            alu_a = rs1_fwd;
        end
    end

    // ALU operand B: rs2 or immediate
    assign alu_b = id_ex_in.alu_src ? id_ex_in.imm : rs2_fwd;

    // Instantiate ALU
    alu u_alu (
        .a          (alu_a),
        .b          (alu_b),
        .op         (id_ex_in.alu_op),
        .word_op    (id_ex_in.word_op),
        .result     (alu_result),
        .zero       (alu_zero),
        .negative   (alu_neg),
        .overflow   (alu_ovf)
    );

    // Instantiate branch unit
    branch_unit u_branch_unit (
        .rs1_data       (rs1_fwd),
        .rs2_data       (rs2_fwd),
        .branch_funct   (id_ex_in.branch_funct),
        .is_branch      (id_ex_in.is_branch),
        .branch_taken   (branch_taken)
    );

    // Branch/Jump target calculation
    always_comb begin
        if (id_ex_in.is_jalr) begin
            // JALR: (rs1 + imm) & ~1
            branch_target = (rs1_fwd + id_ex_in.imm) & ~64'd1;
        end else begin
            // Branch/JAL: PC + offset
            branch_target = id_ex_in.pc + id_ex_in.imm;
        end
    end

    // Output to EX/MEM pipeline register
    always_comb begin
        ex_mem_out.pc = id_ex_in.pc;

        // Result: JAL/JALR write PC+4, others write ALU result
        if (id_ex_in.is_jal || id_ex_in.is_jalr) begin
            ex_mem_out.alu_result = id_ex_in.pc + 64'd4;  // Return address
        end else begin
            ex_mem_out.alu_result = alu_result;
        end

        ex_mem_out.rs2_data = rs2_fwd;  // Store data
        ex_mem_out.rd_addr = id_ex_in.rd_addr;
        ex_mem_out.rd_we = id_ex_in.rd_we;
        ex_mem_out.is_load = id_ex_in.is_load;
        ex_mem_out.is_store = id_ex_in.is_store;
        ex_mem_out.mem_size = id_ex_in.mem_size;
        ex_mem_out.mem_signed = id_ex_in.mem_signed;
        ex_mem_out.branch_taken = branch_taken || id_ex_in.is_jal || id_ex_in.is_jalr;
        ex_mem_out.branch_target = branch_target;
        ex_mem_out.valid = id_ex_in.valid;
    end

endmodule
