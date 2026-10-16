#ifndef YS_PC_SPRITE_UPLOAD_WATCH_H
#define YS_PC_SPRITE_UPLOAD_WATCH_H
#include "sms_runtime.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Original fixed-bank $0427 calls $04BF (64 Y OUTI), which returns
   through $053F to $0436, then falls through 128 X/tile OUTI,
   visiting $053F AGAIN. Only the second return completes an upload.
   Read-only: no Z80, RAM, port, mapper, clock or VDP writes. */
enum { YS_PC_UPLOAD_Y=64,YS_PC_UPLOAD_XT=128,YS_PC_UPLOAD_TOTAL=192 };
typedef struct {
    uint8_t snapshot[YS_PC_UPLOAD_TOTAL];
    bool active, sampled;
    unsigned return_phase,entries,halfway,completed,matched,mismatched,abandoned;
    uint16_t last_pc;
    uint64_t last_step,entry_step,entry_writes;
    uint64_t first_completion,last_completion,bytes_compared,bytes_different;
    uint64_t last_write_delta;
    unsigned first_mismatch_1based,first_expected,first_actual;
    uint32_t first_source_crc,first_vram_crc,last_source_crc,last_vram_crc;
} YsPcSpriteUploadWatch;

bool ys_pc_sprite_upload_watch_sample(YsPcSpriteUploadWatch *watch,
                                      const YsSmsRuntime *runtime);
bool ys_pc_sprite_upload_watch_write(FILE *out,
                                     const YsPcSpriteUploadWatch *watch,
                                     const YsSmsRuntime *runtime,
                                     const char *reason,
                                     unsigned long continued_steps);
#endif
