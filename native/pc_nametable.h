#ifndef YS_PC_NAMETABLE_H
#define YS_PC_NAMETABLE_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Only the source-proven M43 write range $3900-$3EFF. The first
   $3800-$38FF (four 32-cell rows) is NOT in this package. */
enum {
    YS_PC_NT_W=32, YS_PC_NT_H=24,
    YS_PC_NT_VRAM_START=0x3900, YS_PC_NT_RAW_SIZE=1536,
    YS_PC_NT_PACKAGE_BYTES=16+YS_PC_NT_RAW_SIZE
};
typedef struct {
    uint16_t pattern, raw;
    bool horizontal_flip, vertical_flip, palette_1, priority;
} YsPcNameCell;
typedef struct {
    uint8_t raw[YS_PC_NT_RAW_SIZE];
} YsPcNameTable;

bool ys_pc_nametable_load(FILE *file,YsPcNameTable *out);
bool ys_pc_nametable_cell(const YsPcNameTable *table,
                          unsigned column,unsigned row,YsPcNameCell *out);
#endif
