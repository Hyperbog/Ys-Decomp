#ifndef YS_PC_OBJECTS_H
#define YS_PC_OBJECTS_H
#include "pc_records.h"
#include <stdbool.h>
#include <stdint.h>

/* Original bank-0 $1B4E-$1B9A stages up to 16 object slots,
   at WRAM $C230 + $30*index. Unmapped bytes are UNKNOWN, not zero. */
enum { YS_PC_OBJECT_SLOTS=16, YS_PC_OBJECT_SLOT_BYTES=0x30 };
typedef struct {
    uint16_t source_record_pc;
    uint8_t source[4];
    uint16_t value_a, value_b; /* Source transformations, axes unproved. */
    uint8_t work[YS_PC_OBJECT_SLOT_BYTES];
    uint8_t known[YS_PC_OBJECT_SLOT_BYTES];
} YsPcObjectSlot;
typedef struct {
    unsigned group, count;
    YsPcObjectSlot objects[YS_PC_OBJECT_SLOTS];
} YsPcObjectProjection;

/* Projects independently justified stores only; no original game AI, map,
   object-kind-dependent initialization, or collision is implemented. */
bool ys_pc_project_objects(const YsPcRecords *data,unsigned group,
                           YsPcObjectProjection *out);
#endif
