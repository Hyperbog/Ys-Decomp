#ifndef YS_PC_SAT_PROVENANCE_H
#define YS_PC_SAT_PROVENANCE_H
#include "sms_runtime.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Read-only instruction-boundary attribution; detects value changes,
   NOT same-value stores and NOT an independently verified writer opcode. */
enum { YS_PC38_BYTES=192, YS_PC38_Y=64, YS_PC38_MAX_SITES=128 };
typedef struct {
    uint16_t pc;
    uint8_t physical_bank; /* 0-15 ROM; 254 cart RAM; 255 CPU RAM */
    uint64_t changed_bytes;
} YsPcSatChangeSite;
typedef struct {
    uint8_t previous[YS_PC38_BYTES], uploaded[YS_PC38_BYTES];
    uint8_t unique[YS_PC38_BYTES], previous_bank;
    uint16_t previous_pc;
    uint64_t previous_steps, samples, changed, changed_y, changed_xt;
    uint64_t upload_diff_bytes;
    unsigned unique_bytes, upload_count, changed_uploads, equal_uploads;
    unsigned site_count;
    YsPcSatChangeSite sites[YS_PC38_MAX_SITES];
    bool initialized, have_upload;
} YsPcSatProvenance;

bool ys_pc_sat_provenance_sample(YsPcSatProvenance *audit,
                                 const YsSmsRuntime *runtime);
bool ys_pc_sat_provenance_upload(YsPcSatProvenance *audit,
                                 const YsSmsRuntime *runtime);
bool ys_pc_sat_provenance_write(FILE *file,const YsPcSatProvenance *audit,
                                const YsSmsRuntime *runtime,
                                const char *reason,unsigned long steps);
#endif
