// hazard_unit.sv - Hazard Detection Unit
// Part of the tri-mode SoC project
//
// Detects hazards that cannot be resolved by forwarding and generates
// stall/flush signals:
// - Load-use hazard: Load followed by instruction using loaded value
// - Control hazard: Branch/jump taken requires pipeline flush

module hazard_unit
    import types_pkg::*;
    import pipeline_pkg::*;
(
    // IF/ID stage info (decode stage sources)
    input  rf_addr_t    if_id_rs1_addr,
    input  rf_addr_t    if_id_rs2_addr,
    input  logic        if_id_rs1_used,
    input  logic        if_id_rs2_used,

    // ID/EX stage info (for load-use detection)
    input  rf_addr_t    id_ex_rd_addr,
    input  logic        id_ex_is_load,
    input  logic        id_ex_valid,

    // Branch/jump taken (from EX stage)
    input  logic        branch_taken,
    input  pc_t         branch_target,

    // Hazard control outputs
    output logic        stall_if,
    output logic        stall_id,
    output logic        flush_if,
    output logic        flush_id,
    output logic        flush_ex,
    output pc_t         redirect_pc
);

    // Load-use hazard detection
    // If a load in ID/EX writes to a register that IF/ID is reading,
    // we must stall one cycle (cannot forward from load in EX stage)
    logic load_use_hazard;

    always_comb begin
        load_use_hazard = 1'b0;

        if (id_ex_is_load && id_ex_valid && id_ex_rd_addr != '0) begin
            if ((if_id_rs1_used && if_id_rs1_addr == id_ex_rd_addr) ||
                (if_id_rs2_used && if_id_rs2_addr == id_ex_rd_addr)) begin
                load_use_hazard = 1'b1;
            end
        end
    end

    // Control hazard handling
    // When branch/jump is taken, flush IF and ID stages
    always_comb begin
        // Default: no stalls or flushes
        stall_if = 1'b0;
        stall_id = 1'b0;
        flush_if = 1'b0;
        flush_id = 1'b0;
        flush_ex = 1'b0;
        redirect_pc = branch_target;

        if (branch_taken) begin
            // Flush the pipeline on branch taken
            flush_if = 1'b1;
            flush_id = 1'b1;
            flush_ex = 1'b0;  // EX has valid branch, don't flush it
        end else if (load_use_hazard) begin
            // Stall IF and ID, insert bubble in EX
            stall_if = 1'b1;
            stall_id = 1'b1;
            flush_ex = 1'b1;
        end
    end

endmodule
