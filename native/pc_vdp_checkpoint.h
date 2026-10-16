#ifndef YS_PC_VDP_CHECKPOINT_H
#define YS_PC_VDP_CHECKPOINT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "sms_vdp.h"
#include "pc_patterns.h"
#include "pc_nametable.h"

enum {
    YS_PC_VDP_CHECKPOINT_PC=0x0C87,
    YS_PC_VDP_PAYLOAD_BYTES=YS_VRAM_BYTES+YS_CRAM_BYTES+YS_VDP_REGISTERS,
    YS_PC_VDP_FILE_BYTES=16+YS_PC_VDP_PAYLOAD_BYTES
};
typedef struct {
    YsSmsVdp vdp; /* Complete simultaneous source checkpoint memory + registers. */
    uint16_t source_pc;
} YsPcVdpCheckpoint;

bool ys_pc_vdp_checkpoint_save(FILE *file,const YsSmsVdp *vdp,uint16_t pc);
bool ys_pc_vdp_checkpoint_load(FILE *file,YsPcVdpCheckpoint *out);
/* Require exact byte identity of original M44 pattern VRAM and M43
   original name-table data in the same M44 runtime snapshot. */
bool ys_pc_vdp_checkpoint_matches(const YsPcVdpCheckpoint *capture,
                                   const YsPcPatterns *patterns,
                                   const YsPcNameTable *names);
#endif
