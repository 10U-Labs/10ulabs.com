# Verilator Testbench Makefile
# Part of the tri-mode SoC project

# Verilator settings
VERILATOR := verilator
VERILATOR_FLAGS := --cc --exe --build \
    --trace-fst \
    -Wall -Wno-fatal \
    -Wno-WIDTHEXPAND \
    -Wno-WIDTHTRUNC \
    -Wno-UNUSEDSIGNAL \
    -Wno-UNDRIVEN \
    --timing \
    -O3 \
    -CFLAGS "-O3"

# Top module
TOP_MODULE := soc_top

# RTL directories
RTL_ROOT := ../..
PKG_DIR := $(RTL_ROOT)/common/pkg
CORE_DIR := $(RTL_ROOT)/core
MEM_DIR := $(RTL_ROOT)/mem
SOC_DIR := $(RTL_ROOT)/soc

# Source files (order matters for packages)
PKG_FILES := \
    $(PKG_DIR)/types_pkg.sv \
    $(PKG_DIR)/rv64_pkg.sv \
    $(PKG_DIR)/pipeline_pkg.sv

CORE_FILES := \
    $(CORE_DIR)/regfile/regfile.sv \
    $(CORE_DIR)/execute/alu.sv \
    $(CORE_DIR)/execute/branch_unit.sv \
    $(CORE_DIR)/decode/imm_gen.sv \
    $(CORE_DIR)/decode/rv64i_decoder.sv \
    $(CORE_DIR)/decode/decode_stage.sv \
    $(CORE_DIR)/frontend/pc_gen.sv \
    $(CORE_DIR)/frontend/fetch_stage.sv \
    $(CORE_DIR)/execute/execute_stage.sv \
    $(CORE_DIR)/memory/lsu.sv \
    $(CORE_DIR)/memory/memory_stage.sv \
    $(CORE_DIR)/writeback/writeback_stage.sv \
    $(CORE_DIR)/hazard/forwarding_unit.sv \
    $(CORE_DIR)/hazard/hazard_unit.sv \
    $(CORE_DIR)/pipeline/pipeline_regs.sv \
    $(CORE_DIR)/pipeline/core_top.sv

MEM_FILES := \
    $(MEM_DIR)/imem.sv \
    $(MEM_DIR)/dmem.sv

SOC_FILES := \
    $(SOC_DIR)/soc_top.sv

SV_SOURCES := $(PKG_FILES) $(CORE_FILES) $(MEM_FILES) $(SOC_FILES)

# C++ testbench
CPP_SOURCES := tb_top.cpp

# Output directory
OBJ_DIR := obj_dir

# Targets
.PHONY: all build run clean lint

all: build

build: $(OBJ_DIR)/V$(TOP_MODULE)

$(OBJ_DIR)/V$(TOP_MODULE): $(SV_SOURCES) $(CPP_SOURCES)
	$(VERILATOR) $(VERILATOR_FLAGS) \
		--top-module $(TOP_MODULE) \
		--Mdir $(OBJ_DIR) \
		-o V$(TOP_MODULE) \
		$(SV_SOURCES) $(CPP_SOURCES)

run: build
	./$(OBJ_DIR)/V$(TOP_MODULE) +trace +max_cycles=10000

# Run with specific program
run-program: build
	@if [ -z "$(PROGRAM)" ]; then \
		echo "Usage: make run-program PROGRAM=path/to/program.hex"; \
		exit 1; \
	fi
	./$(OBJ_DIR)/V$(TOP_MODULE) +trace +program=$(PROGRAM) +max_cycles=10000

# Lint only (no build)
lint:
	$(VERILATOR) --lint-only \
		-Wall \
		-Wno-WIDTHEXPAND \
		-Wno-WIDTHTRUNC \
		--top-module $(TOP_MODULE) \
		$(SV_SOURCES)

clean:
	rm -rf $(OBJ_DIR)
	rm -f sim.fst sim.vcd

# Show source files
sources:
	@echo "Package files:"
	@echo "  $(PKG_FILES)" | tr ' ' '\n'
	@echo ""
	@echo "Core files:"
	@echo "  $(CORE_FILES)" | tr ' ' '\n'
	@echo ""
	@echo "Memory files:"
	@echo "  $(MEM_FILES)" | tr ' ' '\n'
	@echo ""
	@echo "SoC files:"
	@echo "  $(SOC_FILES)" | tr ' ' '\n'
