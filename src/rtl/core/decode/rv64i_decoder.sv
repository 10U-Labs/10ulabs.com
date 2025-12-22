// rv64i_decoder.sv - RV64I Instruction Decoder
// Part of the tri-mode SoC project
//
// Decodes RV64I base integer instructions and generates control signals.
// Supports: R, I, S, B, U, J type instructions and RV64I W-variants.

module rv64i_decoder
    import types_pkg::*;
    import rv64_pkg::*;
(
    input  instr_t      instr,
    input  logic        valid,

    // Register addresses
    output rf_addr_t    rs1_addr,
    output rf_addr_t    rs2_addr,
    output rf_addr_t    rd_addr,

    // Register usage flags (for hazard detection)
    output logic        rs1_used,
    output logic        rs2_used,
    output logic        rd_we,

    // ALU control
    output alu_op_t     alu_op,
    output logic        alu_src,        // 0=rs2, 1=immediate

    // RV64I W-variant
    output logic        word_op,        // 32-bit operation

    // Branch/Jump control
    output logic        is_branch,
    output logic [2:0]  branch_funct,
    output logic        is_jal,
    output logic        is_jalr,

    // Memory control
    output logic        is_load,
    output logic        is_store,
    output logic [2:0]  mem_size,
    output logic        mem_signed,

    // Exception
    output logic        illegal_instr
);

    // Extract instruction fields
    logic [6:0] opcode;
    logic [2:0] funct3;
    logic [6:0] funct7;

    assign opcode = instr[6:0];
    assign funct3 = instr[14:12];
    assign funct7 = instr[31:25];

    // Register address extraction
    assign rs1_addr = instr[19:15];
    assign rs2_addr = instr[24:20];
    assign rd_addr  = instr[11:7];

    // Main decoder logic
    always_comb begin
        // Default values
        rs1_used = 1'b0;
        rs2_used = 1'b0;
        rd_we = 1'b0;
        alu_op = ALU_ADD;
        alu_src = 1'b0;
        word_op = 1'b0;
        is_branch = 1'b0;
        branch_funct = 3'b0;
        is_jal = 1'b0;
        is_jalr = 1'b0;
        is_load = 1'b0;
        is_store = 1'b0;
        mem_size = 3'b0;
        mem_signed = 1'b0;
        illegal_instr = 1'b0;

        if (valid) begin
            case (opcode)
                // LUI - Load Upper Immediate
                OP_LUI: begin
                    rd_we = 1'b1;
                    alu_op = ALU_PASS_B;
                    alu_src = 1'b1;  // Use immediate
                end

                // AUIPC - Add Upper Immediate to PC
                OP_AUIPC: begin
                    rd_we = 1'b1;
                    alu_op = ALU_ADD;
                    alu_src = 1'b1;  // PC + immediate
                end

                // JAL - Jump and Link
                OP_JAL: begin
                    rd_we = 1'b1;
                    is_jal = 1'b1;
                    alu_op = ALU_ADD;  // Calculate PC+4 for return address
                end

                // JALR - Jump and Link Register
                OP_JALR: begin
                    rs1_used = 1'b1;
                    rd_we = 1'b1;
                    is_jalr = 1'b1;
                    alu_op = ALU_ADD;
                    alu_src = 1'b1;  // rs1 + immediate
                    if (funct3 != 3'b000) begin
                        illegal_instr = 1'b1;
                    end
                end

                // Branches
                OP_BRANCH: begin
                    rs1_used = 1'b1;
                    rs2_used = 1'b1;
                    is_branch = 1'b1;
                    branch_funct = funct3;
                    // Validate branch function
                    if (funct3 == 3'b010 || funct3 == 3'b011) begin
                        illegal_instr = 1'b1;
                    end
                end

                // Loads
                OP_LOAD: begin
                    rs1_used = 1'b1;
                    rd_we = 1'b1;
                    is_load = 1'b1;
                    alu_op = ALU_ADD;
                    alu_src = 1'b1;  // rs1 + offset
                    mem_size = funct3[1:0];
                    mem_signed = ~funct3[2];  // LB/LH/LW are signed, LBU/LHU/LWU are unsigned
                    // Validate load size
                    if (funct3 == 3'b111) begin
                        illegal_instr = 1'b1;
                    end
                end

                // Stores
                OP_STORE: begin
                    rs1_used = 1'b1;
                    rs2_used = 1'b1;
                    is_store = 1'b1;
                    alu_op = ALU_ADD;
                    alu_src = 1'b1;  // rs1 + offset
                    mem_size = funct3[1:0];
                    // Validate store size
                    if (funct3[2] == 1'b1 || funct3 == 3'b111) begin
                        illegal_instr = 1'b1;
                    end
                end

                // Integer Register-Immediate
                OP_OP_IMM: begin
                    rs1_used = 1'b1;
                    rd_we = 1'b1;
                    alu_src = 1'b1;  // Use immediate
                    case (funct3)
                        F3_ADD_SUB: alu_op = ALU_ADD;  // ADDI (no SUBI)
                        F3_SLT:     alu_op = ALU_SLT;
                        F3_SLTU:    alu_op = ALU_SLTU;
                        F3_XOR:     alu_op = ALU_XOR;
                        F3_OR:      alu_op = ALU_OR;
                        F3_AND:     alu_op = ALU_AND;
                        F3_SLL: begin
                            alu_op = ALU_SLL;
                            // SLLI: funct7[6:1] must be 000000 for RV64I
                            if (funct7[6:1] != 6'b000000) begin
                                illegal_instr = 1'b1;
                            end
                        end
                        F3_SRL_SRA: begin
                            // SRLI vs SRAI distinguished by funct7[5]
                            if (funct7[6:1] == 6'b000000) begin
                                alu_op = ALU_SRL;
                            end else if (funct7[6:1] == 6'b010000) begin
                                alu_op = ALU_SRA;
                            end else begin
                                illegal_instr = 1'b1;
                            end
                        end
                    endcase
                end

                // Integer Register-Register
                OP_OP: begin
                    rs1_used = 1'b1;
                    rs2_used = 1'b1;
                    rd_we = 1'b1;
                    alu_src = 1'b0;  // Use rs2
                    case (funct3)
                        F3_ADD_SUB: begin
                            if (funct7 == F7_NORMAL) begin
                                alu_op = ALU_ADD;
                            end else if (funct7 == F7_ALT) begin
                                alu_op = ALU_SUB;
                            end else begin
                                illegal_instr = 1'b1;
                            end
                        end
                        F3_SLL: begin
                            alu_op = ALU_SLL;
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                        F3_SLT: begin
                            alu_op = ALU_SLT;
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                        F3_SLTU: begin
                            alu_op = ALU_SLTU;
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                        F3_XOR: begin
                            alu_op = ALU_XOR;
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                        F3_SRL_SRA: begin
                            if (funct7 == F7_NORMAL) begin
                                alu_op = ALU_SRL;
                            end else if (funct7 == F7_ALT) begin
                                alu_op = ALU_SRA;
                            end else begin
                                illegal_instr = 1'b1;
                            end
                        end
                        F3_OR: begin
                            alu_op = ALU_OR;
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                        F3_AND: begin
                            alu_op = ALU_AND;
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                    endcase
                end

                // RV64I 32-bit Immediate (ADDIW, SLLIW, SRLIW, SRAIW)
                OP_OP_IMM_32: begin
                    rs1_used = 1'b1;
                    rd_we = 1'b1;
                    alu_src = 1'b1;
                    word_op = 1'b1;
                    case (funct3)
                        F3_ADD_SUB: alu_op = ALU_ADD;  // ADDIW
                        F3_SLL: begin
                            alu_op = ALU_SLL;  // SLLIW
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                        F3_SRL_SRA: begin
                            if (funct7 == F7_NORMAL) begin
                                alu_op = ALU_SRL;  // SRLIW
                            end else if (funct7 == F7_ALT) begin
                                alu_op = ALU_SRA;  // SRAIW
                            end else begin
                                illegal_instr = 1'b1;
                            end
                        end
                        default: illegal_instr = 1'b1;
                    endcase
                end

                // RV64I 32-bit Register (ADDW, SUBW, SLLW, SRLW, SRAW)
                OP_OP_32: begin
                    rs1_used = 1'b1;
                    rs2_used = 1'b1;
                    rd_we = 1'b1;
                    alu_src = 1'b0;
                    word_op = 1'b1;
                    case (funct3)
                        F3_ADD_SUB: begin
                            if (funct7 == F7_NORMAL) begin
                                alu_op = ALU_ADD;  // ADDW
                            end else if (funct7 == F7_ALT) begin
                                alu_op = ALU_SUB;  // SUBW
                            end else begin
                                illegal_instr = 1'b1;
                            end
                        end
                        F3_SLL: begin
                            alu_op = ALU_SLL;  // SLLW
                            if (funct7 != F7_NORMAL) illegal_instr = 1'b1;
                        end
                        F3_SRL_SRA: begin
                            if (funct7 == F7_NORMAL) begin
                                alu_op = ALU_SRL;  // SRLW
                            end else if (funct7 == F7_ALT) begin
                                alu_op = ALU_SRA;  // SRAW
                            end else begin
                                illegal_instr = 1'b1;
                            end
                        end
                        default: illegal_instr = 1'b1;
                    endcase
                end

                default: begin
                    illegal_instr = 1'b1;
                end
            endcase
        end
    end

endmodule
