// rv64_pkg.sv - RV64I opcode, function, and ALU operation definitions
// Part of the tri-mode SoC project

package rv64_pkg;

    // RV64I Opcodes (bits [6:0] of instruction)
    typedef enum logic [6:0] {
        OP_LUI      = 7'b0110111,   // Load Upper Immediate
        OP_AUIPC    = 7'b0010111,   // Add Upper Immediate to PC
        OP_JAL      = 7'b1101111,   // Jump and Link
        OP_JALR     = 7'b1100111,   // Jump and Link Register
        OP_BRANCH   = 7'b1100011,   // Conditional Branch
        OP_LOAD     = 7'b0000011,   // Load
        OP_STORE    = 7'b0100011,   // Store
        OP_OP_IMM   = 7'b0010011,   // Integer Register-Immediate
        OP_OP       = 7'b0110011,   // Integer Register-Register
        OP_OP_IMM_32 = 7'b0011011,  // RV64I 32-bit Immediate (ADDIW, etc.)
        OP_OP_32    = 7'b0111011,   // RV64I 32-bit Register-Register (ADDW, etc.)
        OP_MISC_MEM = 7'b0001111,   // FENCE (not implemented in Phase 1)
        OP_SYSTEM   = 7'b1110011    // ECALL/EBREAK/CSR (not implemented in Phase 1)
    } opcode_t;

    // ALU operation codes
    typedef enum logic [3:0] {
        ALU_ADD     = 4'b0000,      // Addition
        ALU_SUB     = 4'b0001,      // Subtraction
        ALU_AND     = 4'b0010,      // Bitwise AND
        ALU_OR      = 4'b0011,      // Bitwise OR
        ALU_XOR     = 4'b0100,      // Bitwise XOR
        ALU_SLT     = 4'b0101,      // Set Less Than (signed)
        ALU_SLTU    = 4'b0110,      // Set Less Than (unsigned)
        ALU_SLL     = 4'b0111,      // Shift Left Logical
        ALU_SRL     = 4'b1000,      // Shift Right Logical
        ALU_SRA     = 4'b1001,      // Shift Right Arithmetic
        ALU_PASS_A  = 4'b1010,      // Pass operand A (for LUI)
        ALU_PASS_B  = 4'b1011       // Pass operand B (for AUIPC immediate)
    } alu_op_t;

    // Branch function codes (funct3 for BRANCH opcode)
    typedef enum logic [2:0] {
        BR_BEQ  = 3'b000,           // Branch if Equal
        BR_BNE  = 3'b001,           // Branch if Not Equal
        BR_BLT  = 3'b100,           // Branch if Less Than (signed)
        BR_BGE  = 3'b101,           // Branch if Greater or Equal (signed)
        BR_BLTU = 3'b110,           // Branch if Less Than (unsigned)
        BR_BGEU = 3'b111            // Branch if Greater or Equal (unsigned)
    } branch_funct_t;

    // Load/Store size (funct3 for LOAD/STORE opcodes)
    typedef enum logic [2:0] {
        MEM_BYTE    = 3'b000,       // LB/SB - byte
        MEM_HALF    = 3'b001,       // LH/SH - halfword
        MEM_WORD    = 3'b010,       // LW/SW - word
        MEM_DWORD   = 3'b011,       // LD/SD - doubleword
        MEM_BYTE_U  = 3'b100,       // LBU - unsigned byte
        MEM_HALF_U  = 3'b101,       // LHU - unsigned halfword
        MEM_WORD_U  = 3'b110        // LWU - unsigned word
    } mem_size_t;

    // funct3 for OP-IMM and OP instructions
    typedef enum logic [2:0] {
        F3_ADD_SUB  = 3'b000,       // ADD/SUB/ADDI
        F3_SLL      = 3'b001,       // SLL/SLLI
        F3_SLT      = 3'b010,       // SLT/SLTI
        F3_SLTU     = 3'b011,       // SLTU/SLTIU
        F3_XOR      = 3'b100,       // XOR/XORI
        F3_SRL_SRA  = 3'b101,       // SRL/SRA/SRLI/SRAI
        F3_OR       = 3'b110,       // OR/ORI
        F3_AND      = 3'b111        // AND/ANDI
    } alu_funct3_t;

    // funct7 bit 5 for distinguishing ADD/SUB, SRL/SRA
    parameter logic [6:0] F7_NORMAL = 7'b0000000;
    parameter logic [6:0] F7_ALT    = 7'b0100000;  // SUB, SRA

    // Instruction field extraction helper functions
    function automatic logic [6:0] get_opcode(input logic [31:0] instr);
        return instr[6:0];
    endfunction

    function automatic logic [4:0] get_rd(input logic [31:0] instr);
        return instr[11:7];
    endfunction

    function automatic logic [2:0] get_funct3(input logic [31:0] instr);
        return instr[14:12];
    endfunction

    function automatic logic [4:0] get_rs1(input logic [31:0] instr);
        return instr[19:15];
    endfunction

    function automatic logic [4:0] get_rs2(input logic [31:0] instr);
        return instr[24:20];
    endfunction

    function automatic logic [6:0] get_funct7(input logic [31:0] instr);
        return instr[31:25];
    endfunction

endpackage
