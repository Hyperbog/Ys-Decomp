#ifndef YS_PC43_SPRITE_GATE_H
#define YS_PC43_SPRITE_GATE_H
#include "sms_runtime.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Read-only trace of physical bank6 $9966 source gate on the
   original controlled M45 continuation. No source-state mutation. */
enum { YS_PC43_MAX_ENTRIES=64 };
typedef struct {
    unsigned long entry_iteration, gate_iteration;
    uint64_t entry_cpu_step, gate_cpu_step;
    uint8_t slot2, selector, c198_entry, c199_entry, c1b9_entry;
    uint8_t a_gate, c198_gate, f_gate, iff2_gate;
    bool or_seen, gate_seen, successor_seen, irq_during_gate;
    uint16_t successor_pc;
    uint64_t irq_before, irq_after;
} YsPc43GateEvent;
typedef struct {
    YsPc43GateEvent entries[YS_PC43_MAX_ENTRIES];
    unsigned count, or_hits, gate_hits, call_sites, producer_entries;
    unsigned skip_targets, orphan_gates, branch_zero, branch_nonzero;
    unsigned branch_mismatch, irq_gate;
    unsigned long observed_iterations;
    bool jump_pending;
    unsigned pending_entry;
} YsPc43SpriteGate;

bool ys_pc43_gate_pre(YsPc43SpriteGate *watch,const YsSmsRuntime *rt,
                      unsigned long iteration);
bool ys_pc43_gate_post(YsPc43SpriteGate *watch,const YsSmsRuntime *rt,
                       unsigned long iteration);
bool ys_pc43_gate_write(FILE *file,const YsPc43SpriteGate *watch,
                        const YsSmsRuntime *rt,const char *reason,
                        unsigned long executed);
#endif
