#ifndef YS_PC40_ROUTE_H
#define YS_PC40_ROUTE_H
#include "sms_runtime.h"
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>

/* Same original fixed-controller schedule, 300k prefix then 300k
   additional bounded iterations. This observer never mutates CPU state. */
enum { YS_PC40_EVENTS=12, YS_PC40_PHASES=2 };
typedef struct {
    uint32_t hits;
    uint64_t first_step,last_step;
    uint8_t first_selector,first_slot2;
} YsPc40Event;
typedef struct {
    YsPc40Event events[YS_PC40_PHASES][YS_PC40_EVENTS];
    unsigned long seen_iterations;
    bool prefix_seen;
    uint16_t prefix_pc;
    uint8_t prefix_selector,prefix_slot1,prefix_slot2;
    uint64_t prefix_irq,prefix_vblank;
    uint32_t prefix_sprite[5],prefix_collisions;
} YsPc40Route;
bool ys_pc40_route_sample(YsPc40Route *watch,const YsSmsRuntime *rt,
                           unsigned long iteration);
bool ys_pc40_route_mark_prefix(YsPc40Route *watch,const YsSmsRuntime *rt,
                                unsigned long iteration,
                                const uint32_t sprite_counts[5],
                                uint32_t collisions);
bool ys_pc40_route_write(FILE *file,const YsPc40Route *watch,
                          const YsSmsRuntime *rt,const char *reason,
                          unsigned long executed);
#endif
