#ifndef YS_PC_TILES_H
#define YS_PC_TILES_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

enum {
    YS_PC_TILE_COUNT=176, YS_PC_TILE_BYTES=32,
    YS_PC_TILE_PIXELS=64, YS_PC_ATLAS_W=128, YS_PC_ATLAS_H=88,
    YS_PC_TILE_FILE_HEADER=16
};
/* All grayscale values are diagnostic indices, NOT Ys colors.
   Asset file must be generated from source-only bank3, not a ROM. */
typedef struct { uint8_t index[YS_PC_TILE_COUNT][YS_PC_TILE_PIXELS]; } YsPcTiles;
bool ys_pc_tiles_decode(const uint8_t *mode4, unsigned length,
                        YsPcTiles *out);
bool ys_pc_tiles_load(FILE *fp,YsPcTiles *out);
void ys_pc_tiles_grayscale(const YsPcTiles *tiles,
                           uint8_t rgb[YS_PC_ATLAS_W*YS_PC_ATLAS_H*3]);
#endif
