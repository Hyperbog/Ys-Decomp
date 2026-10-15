#ifndef YS_PC_SPRITE_SAT_H
#define YS_PC_SPRITE_SAT_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Original physical bank6 $8000: 64 pointer words, followed by
   6322 count/delta/pair bytes $8080-$9931. Research, not a player
   sprite, original world coordinate or frame selection. */
enum {
    YS_PC_SPRITE_RECORDS=64,YS_PC_SPRITE_STREAM_BYTES=6322,
    YS_PC_SPRITE_POINTER_BYTES=128,
    YS_PC_SPRITE_PACKAGE_BYTES=16+YS_PC_SPRITE_POINTER_BYTES+
                               YS_PC_SPRITE_STREAM_BYTES,
    YS_PC_SAT_Y_BYTES=64,YS_PC_SAT_XT_BYTES=128,
    YS_PC_SAT_BYTES=YS_PC_SAT_Y_BYTES+YS_PC_SAT_XT_BYTES
};
typedef struct {
    uint16_t pointers[YS_PC_SPRITE_RECORDS]; /* CPU $8080..$9931 */
    uint8_t stream[YS_PC_SPRITE_STREAM_BYTES];
} YsPcSpriteRecords;
typedef struct {
    uint8_t y[YS_PC_SAT_Y_BYTES]; /* emulated $DD00 -> VRAM $3F00 */
    uint8_t xt[YS_PC_SAT_XT_BYTES]; /* $DD40 -> VRAM $3F80 */
    uint8_t count;                /* bounded original source count */
} YsPcSatBuffer;

/* Strict version/size/CRC/pointer-partition loader. Does not use
   an SMS ROM and does not load any sprite artwork. */
bool ys_pc_sprite_records_load(FILE *file,YsPcSpriteRecords *out);
/* Reconstruct the original $9932 SAT stage for supplied synthetic
   $C210/$C211 origin bytes. No live game mapper/player implied. */
bool ys_pc_sprite_stage(const YsPcSpriteRecords *records,unsigned index,
                        uint8_t origin_y,uint8_t origin_x,
                        YsPcSatBuffer *out);
#endif
