// forwarding_unit.sv - Data Forwarding Unit
// Part of the tri-mode SoC project
//
// Detects data hazards and generates forwarding control signals.
// Forwards from EX/MEM or MEM/WB stages to avoid stalls when possible.

module forwarding_unit
    import types_pkg::*;
    import pipeline_pkg::*;
(
    // Decode/Execute stage source registers
    input  rf_addr_t    id_ex_rs1_addr,
    input  rf_addr_t    id_ex_rs2_addr,

    // Execute/Memory stage destination
    input  rf_addr_t    ex_mem_rd_addr,
    input  logic        ex_mem_rd_we,
    input  logic        ex_mem_valid,

    // Memory/Writeback stage destination
    input  rf_addr_t    mem_wb_rd_addr,
    input  logic        mem_wb_rd_we,
    input  logic        mem_wb_valid,

    // Forwarding control outputs
    output fwd_sel_t    fwd_rs1,
    output fwd_sel_t    fwd_rs2
);

    // Forwarding for RS1
    always_comb begin
        fwd_rs1 = FWD_NONE;

        // EX/MEM has priority (more recent value)
        if (ex_mem_rd_we && ex_mem_valid &&
            ex_mem_rd_addr != '0 &&
            ex_mem_rd_addr == id_ex_rs1_addr) begin
            fwd_rs1 = FWD_EX_MEM;
        end
        // MEM/WB forwarding (if not already forwarded from EX/MEM)
        else if (mem_wb_rd_we && mem_wb_valid &&
                 mem_wb_rd_addr != '0 &&
                 mem_wb_rd_addr == id_ex_rs1_addr) begin
            fwd_rs1 = FWD_MEM_WB;
        end
    end

    // Forwarding for RS2
    always_comb begin
        fwd_rs2 = FWD_NONE;

        // EX/MEM has priority (more recent value)
        if (ex_mem_rd_we && ex_mem_valid &&
            ex_mem_rd_addr != '0 &&
            ex_mem_rd_addr == id_ex_rs2_addr) begin
            fwd_rs2 = FWD_EX_MEM;
        end
        // MEM/WB forwarding (if not already forwarded from EX/MEM)
        else if (mem_wb_rd_we && mem_wb_valid &&
                 mem_wb_rd_addr != '0 &&
                 mem_wb_rd_addr == id_ex_rs2_addr) begin
            fwd_rs2 = FWD_MEM_WB;
        end
    end

endmodule
