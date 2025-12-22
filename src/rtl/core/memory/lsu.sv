// lsu.sv - Load-Store Unit
// Part of the tri-mode SoC project
//
// Handles load/store address generation and data formatting:
// - Byte enable generation for stores
// - Data alignment for stores
// - Data extraction and sign extension for loads

module lsu
    import types_pkg::*;
    import rv64_pkg::*;
(
    // Memory address (from ALU)
    input  xlen_t       addr,

    // Store data
    input  xlen_t       store_data,

    // Load/Store control
    input  logic [2:0]  mem_size,
    input  logic        mem_signed,
    input  logic        is_load,
    input  logic        is_store,

    // Data memory interface
    output xlen_t       dmem_addr,
    output xlen_t       dmem_wdata,
    output byte_en_t    dmem_be,
    output logic        dmem_we,
    output logic        dmem_req,
    input  xlen_t       dmem_rdata,

    // Load result
    output xlen_t       load_data
);

    // Byte offset within doubleword
    logic [2:0] byte_offset;
    assign byte_offset = addr[2:0];

    // Memory interface signals
    assign dmem_addr = {addr[63:3], 3'b000};  // Align to 8-byte boundary
    assign dmem_we = is_store;
    assign dmem_req = is_load || is_store;

    // Byte enable generation for stores
    always_comb begin
        dmem_be = 8'b0;
        if (is_store) begin
            case (mem_size)
                MEM_BYTE:  dmem_be = 8'b0000_0001 << byte_offset;
                MEM_HALF:  dmem_be = 8'b0000_0011 << byte_offset;
                MEM_WORD:  dmem_be = 8'b0000_1111 << byte_offset;
                MEM_DWORD: dmem_be = 8'b1111_1111;
                default:   dmem_be = 8'b0;
            endcase
        end
    end

    // Store data alignment
    always_comb begin
        case (mem_size)
            MEM_BYTE:  dmem_wdata = {8{store_data[7:0]}};
            MEM_HALF:  dmem_wdata = {4{store_data[15:0]}};
            MEM_WORD:  dmem_wdata = {2{store_data[31:0]}};
            MEM_DWORD: dmem_wdata = store_data;
            default:   dmem_wdata = store_data;
        endcase
    end

    // Load data extraction and sign extension
    always_comb begin
        load_data = '0;
        if (is_load) begin
            case (mem_size)
                MEM_BYTE: begin
                    // Extract byte based on offset
                    logic [7:0] byte_val;
                    byte_val = dmem_rdata[byte_offset*8 +: 8];
                    load_data = mem_signed ? {{56{byte_val[7]}}, byte_val} : {56'b0, byte_val};
                end
                MEM_BYTE_U: begin
                    logic [7:0] byte_val;
                    byte_val = dmem_rdata[byte_offset*8 +: 8];
                    load_data = {56'b0, byte_val};
                end
                MEM_HALF: begin
                    logic [15:0] half_val;
                    half_val = dmem_rdata[{byte_offset[2:1], 4'b0} +: 16];
                    load_data = mem_signed ? {{48{half_val[15]}}, half_val} : {48'b0, half_val};
                end
                MEM_HALF_U: begin
                    logic [15:0] half_val;
                    half_val = dmem_rdata[{byte_offset[2:1], 4'b0} +: 16];
                    load_data = {48'b0, half_val};
                end
                MEM_WORD: begin
                    logic [31:0] word_val;
                    word_val = byte_offset[2] ? dmem_rdata[63:32] : dmem_rdata[31:0];
                    load_data = mem_signed ? {{32{word_val[31]}}, word_val} : {32'b0, word_val};
                end
                MEM_WORD_U: begin
                    logic [31:0] word_val;
                    word_val = byte_offset[2] ? dmem_rdata[63:32] : dmem_rdata[31:0];
                    load_data = {32'b0, word_val};
                end
                MEM_DWORD: begin
                    load_data = dmem_rdata;
                end
                default: begin
                    load_data = dmem_rdata;
                end
            endcase
        end
    end

endmodule
