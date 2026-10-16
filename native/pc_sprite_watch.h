#ifndef YS_PC_SPRITE_WATCH_H
#define YS_PC_SPRITE_WATCH_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include "sms_runtime.h"

enum { YS_PC_SPRITE_WATCH_EVENTS=5 };
typedef struct {
    uint16_t pc,ix,dd00,dd40;
    uint8_t slot1,slot2,mapper_control,bank_select2;
    uint8_t selector_c199,origin_c210,origin_c211,c100;
    uint8_t vdp_reg0,vdp_reg1,vdp_reg5,vdp_reg6;
    bool display_enabled;
    uint64_t steps,irqs,vblanks,vram_writes,cram_writes;
} YsPcSpriteWatchEvent;
typedef struct {
    bool seen[YS_PC_SPRITE_WATCH_EVENTS];
    unsigned counts[YS_PC_SPRITE_WATCH_EVENTS];
    YsPcSpriteWatchEvent events[YS_PC_SPRITE_WATCH_EVENTS];
} YsPcSpriteWatch;

/* Passive original PC event sampler. Watch fixed bank0 caller
   $26F3, mapper write $26F5, call $2704, SAT upload $0427;
   bank6 $9932 only qualifies with physical bank6 in slot2.
   This does not cause or infer a sprite/player gameplay event. */
bool ys_pc_sprite_watch_sample(YsPcSpriteWatch *watch,
                               const YsSmsRuntime *runtime);
bool ys_pc_sprite_watch_write(FILE *out,const YsPcSpriteWatch *watch,
                              const YsSmsRuntime *runtime,
                              const char *stop_reason,
                              unsigned long continued_steps);
#endif
