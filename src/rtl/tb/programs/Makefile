# Test Programs Makefile
# Part of the tri-mode SoC project
#
# Requires RISC-V toolchain (riscv64-unknown-elf-*)

# Toolchain
CROSS_COMPILE := riscv64-unknown-elf-
AS := $(CROSS_COMPILE)as
LD := $(CROSS_COMPILE)ld
OBJCOPY := $(CROSS_COMPILE)objcopy
OBJDUMP := $(CROSS_COMPILE)objdump

# Flags
ASFLAGS := -march=rv64i -mabi=lp64

# Linker script (text starts at reset vector)
LDFLAGS := -Ttext=0x80000000 -nostdlib

# Directories
ASM_DIR := asm
BIN_DIR := bin

# Find all assembly files
ASM_SRCS := $(wildcard $(ASM_DIR)/*.S)
TESTS := $(patsubst $(ASM_DIR)/%.S,%,$(ASM_SRCS))

# Output files
ELFS := $(patsubst %,$(BIN_DIR)/%.elf,$(TESTS))
BINS := $(patsubst %,$(BIN_DIR)/%.bin,$(TESTS))
HEXS := $(patsubst %,$(BIN_DIR)/%.hex,$(TESTS))
DUMPS := $(patsubst %,$(BIN_DIR)/%.dump,$(TESTS))

.PHONY: all clean list

all: $(BIN_DIR) $(HEXS) $(DUMPS)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Assemble
$(BIN_DIR)/%.o: $(ASM_DIR)/%.S | $(BIN_DIR)
	$(AS) $(ASFLAGS) -o $@ $<

# Link
$(BIN_DIR)/%.elf: $(BIN_DIR)/%.o
	$(LD) $(LDFLAGS) -o $@ $<

# Binary
$(BIN_DIR)/%.bin: $(BIN_DIR)/%.elf
	$(OBJCOPY) -O binary $< $@

# Hex (for $readmemh)
$(BIN_DIR)/%.hex: $(BIN_DIR)/%.bin
	xxd -e -c 4 $< | awk '{print $$2}' > $@

# Disassembly for debugging
$(BIN_DIR)/%.dump: $(BIN_DIR)/%.elf
	$(OBJDUMP) -d $< > $@

clean:
	rm -rf $(BIN_DIR)

list:
	@echo "Available tests:"
	@for t in $(TESTS); do echo "  $$t"; done

# Check toolchain
check-toolchain:
	@which $(AS) > /dev/null || (echo "Error: RISC-V toolchain not found. Install riscv64-unknown-elf-*" && exit 1)
	@echo "Toolchain found: $(AS)"
