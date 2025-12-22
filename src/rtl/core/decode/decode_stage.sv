// decode_stage.sv - Instruction Decode Stage
// Part of the tri-mode SoC project
//
// Responsibilities:
// - Decode instruction
// - Read register file
// - Generate control signals
// - Select appropriate immediate

module decode_stage
    import types_pkg::*;
    import rv64_pkg::*;
    import pipeline_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,

    // Input from IF/ID pipeline register
    input  if_id_t      if_id_in,

    // Register file read ports (directly connected)
    output rf_addr_t    rf_rs1_addr,
    output rf_addr_t    rf_rs2_addr,
    input  xlen_t       rf_rs1_data,
    input  xlen_t       rf_rs2_data,

    // Hazard signals
    output logic        rs1_used,
    output logic        rs2_used,
    output rf_addr_t    rs1_addr,
    output rf_addr_t    rs2_addr,

    // Output to ID/EX pipeline register
    output id_ex_t      id_ex_out
);

    // Decoder outputs
    rf_addr_t   dec_rs1_addr;
    rf_addr_t   dec_rs2_addr;
    rf_addr_t   dec_rd_addr;
    logic       dec_rs1_used;
    logic       dec_rs2_used;
    logic       dec_rd_we;
    alu_op_t    dec_alu_op;
    logic       dec_alu_src;
    logic       dec_word_op;
    logic       dec_is_branch;
    logic [2:0] dec_branch_funct;
    logic       dec_is_jal;
    logic       dec_is_jalr;
    logic       dec_is_load;
    logic       dec_is_store;
    logic [2:0] dec_mem_size;
    logic       dec_mem_signed;
    logic       dec_illegal_instr;

    // Immediate generator outputs
    xlen_t      imm_i, imm_s, imm_b, imm_u, imm_j;

    // Selected immediate
    xlen_t      imm_selected;

    // Instantiate decoder
    rv64i_decoder u_decoder (
        .instr          (if_id_in.instr),
        .valid          (if_id_in.valid),
        .rs1_addr       (dec_rs1_addr),
        .rs2_addr       (dec_rs2_addr),
        .rd_addr        (dec_rd_addr),
        .rs1_used       (dec_rs1_used),
        .rs2_used       (dec_rs2_used),
        .rd_we          (dec_rd_we),
        .alu_op         (dec_alu_op),
        .alu_src        (dec_alu_src),
        .word_op        (dec_word_op),
        .is_branch      (dec_is_branch),
        .branch_funct   (dec_branch_funct),
        .is_jal         (dec_is_jal),
        .is_jalr        (dec_is_jalr),
        .is_load        (dec_is_load),
        .is_store       (dec_is_store),
        .mem_size       (dec_mem_size),
        .mem_signed     (dec_mem_signed),
        .illegal_instr  (dec_illegal_instr)
    );

    // Instantiate immediate generator
    imm_gen u_imm_gen (
        .instr          (if_id_in.instr),
        .imm_i          (imm_i),
        .imm_s          (imm_s),
        .imm_b          (imm_b),
        .imm_u          (imm_u),
        .imm_j          (imm_j)
    );

    // Connect register file read addresses
    assign rf_rs1_addr = dec_rs1_addr;
    assign rf_rs2_addr = dec_rs2_addr;

    // Hazard detection outputs
    assign rs1_used = dec_rs1_used;
    assign rs2_used = dec_rs2_used;
    assign rs1_addr = dec_rs1_addr;
    assign rs2_addr = dec_rs2_addr;

    // Immediate selection based on instruction type
    always_comb begin
        case (if_id_in.instr[6:0])
            OP_LUI, OP_AUIPC:
                imm_selected = imm_u;
            OP_JAL:
                imm_selected = imm_j;
            OP_BRANCH:
                imm_selected = imm_b;
            OP_STORE:
                imm_selected = imm_s;
            default:  // JALR, LOAD, OP-IMM, OP-IMM-32
                imm_selected = imm_i;
        endcase
    end

    // Output to ID/EX pipeline register
    always_comb begin
        id_ex_out.pc = if_id_in.pc;
        id_ex_out.rs1_data = rf_rs1_data;
        id_ex_out.rs2_data = rf_rs2_data;
        id_ex_out.rs1_addr = dec_rs1_addr;
        id_ex_out.rs2_addr = dec_rs2_addr;
        id_ex_out.rd_addr = dec_rd_addr;
        id_ex_out.imm = imm_selected;
        id_ex_out.rd_we = dec_rd_we;
        id_ex_out.alu_op = dec_alu_op;
        id_ex_out.alu_src = dec_alu_src;
        id_ex_out.word_op = dec_word_op;
        id_ex_out.is_branch = dec_is_branch;
        id_ex_out.branch_funct = dec_branch_funct;
        id_ex_out.is_jal = dec_is_jal;
        id_ex_out.is_jalr = dec_is_jalr;
        id_ex_out.is_load = dec_is_load;
        id_ex_out.is_store = dec_is_store;
        id_ex_out.mem_size = dec_mem_size;
        id_ex_out.mem_signed = dec_mem_signed;
        id_ex_out.valid = if_id_in.valid && !dec_illegal_instr;
    end

endmodule
