#ifndef YS_PC_PATTERNS_H
#define YS_PC_PATTERNS_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include "pc_nametable.h"

/* M44 source-backed $0000-$2FFF, 384 patterns; upper 128 are
   NOT in the exported source transfer. No CRAM palette is included. */
enum { YS_PC_PATTERNS_COUNT=384,YS_PC_PATTERN_BYTES=12288,
       YS_PC_PATTERN_PACKAGE_BYTES=12304,
       YS_PC_PREVIEW_W=256,YS_PC_PREVIEW_H=192,
       YS_PC_PATTERN_UNRESOLVED=255 };
typedef struct {
    uint8_t raw[YS_PC_PATTERN_BYTES];
} YsPcPatterns;
typedef struct {
    unsigned matched_cells,unresolved_cells;
} YsPcPatternCoverage;

bool ys_pc_patterns_load(FILE *file,YsPcPatterns *out);
bool ys_pc_pattern_pixel(const YsPcPatterns *patterns,unsigned tile,
                         unsigned x,unsigned y,uint8_t *out);
/* Diagnostic 32x24 composite of original transferred name words
   and original pattern bytes. Pixel index 255 marks UNRESOLVED
   pattern index >=384. NOT a live/original-color game screenshot. */
bool ys_pc_patterns_preview(const YsPcPatterns *patterns,
                            const YsPcNameTable *names,
                            uint8_t output[YS_PC_PREVIEW_W*YS_PC_PREVIEW_H],
                            YsPcPatternCoverage *coverage);
#endif
