#ifndef YS_PC_SOURCE_WATCH_H
#define YS_PC_SOURCE_WATCH_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include "sms_runtime.h"

/* Original source positions, not verified active gameplay events. */
enum { YS_PC_WATCH_EVENTS=5 };
typedef struct {
    uint16_t pc,ix;
    uint8_t slot1,slot2,bank_select2,mapper_control;
    uint8_t c100,c119,c181,c20d,c20e,c210,c211;
    uint8_t ix13,ix14,ix16,ix17;
    uint64_t steps,irqs,vblanks;
} YsPcSourceWatchEvent;
typedef struct {
    bool seen[YS_PC_WATCH_EVENTS];
    YsPcSourceWatchEvent events[YS_PC_WATCH_EVENTS];
    unsigned counts[YS_PC_WATCH_EVENTS];
    unsigned observed_collision_calls;
} YsPcSourceWatch;

/* Observe CPU state BEFORE source opcode execution; never step or
   change the original bus/VDP/cpu. Only count PC addresses while
   physical bank 1 is actually mapped into slot 1. */
bool ys_pc_source_watch_sample(YsPcSourceWatch *out,
                               const YsSmsRuntime *runtime);
/* JSON serialization of observations only, with explicit outcome.
   Reaching a PC is not proof of a playable area or player identity. */
bool ys_pc_source_watch_write(FILE *file,const YsPcSourceWatch *watch,
                               const YsSmsRuntime *runtime,
                               const char *stop_reason,
                               unsigned long executed);
#endif
