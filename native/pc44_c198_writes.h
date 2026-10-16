#ifndef YS_PC44_C198_WRITES_H
#define YS_PC44_C198_WRITES_H
#include "sms_runtime.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Every successful PHYSICAL WRAM C198 write, including identical-value
   stores, through the original reset/M45 and post-M45 source runtime.
   Does not intercept SRAM or failed ROM stores. */
enum { YS_PC44_MAX_WRITES=256 };
typedef struct {
    unsigned phase;
    unsigned long iteration;
    uint64_t cpu_step;
    uint16_t logical,pc,hl,de,bc;
    uint8_t bank, before,after,a,f,selector,slot2,irq,source_at_hl;
} YsPc44Write;
typedef struct {
    YsZ80 *cpu;
    unsigned phase;
    unsigned long iteration;
    YsPc44Write writes[YS_PC44_MAX_WRITES];
    unsigned count,phase_counts[2],same[2],changed[2],aliases[2];
    bool overflow;
} YsPc44Writer;
void ys_pc44_c198_hook(void *context,uint16_t logical,uint16_t physical,
                       uint8_t before,uint8_t after);
bool ys_pc44_set_phase(YsPc44Writer *writer,unsigned phase);
bool ys_pc44_write_report(FILE *out,const YsPc44Writer *writer,
                          const YsSmsRuntime *runtime,
                          const char *reason,unsigned long steps);
#endif
