#ifndef YS_PC_COLLISION_H
#define YS_PC_COLLISION_H

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* Original bank4 $8000-$807B box data. Bank1 caller mapper state
   and playable-area collision semantics remain unobserved. */
enum { YS_PC_COLLISION_BOXES=31, YS_PC_COLLISION_STRIDE=4,
       YS_PC_COLLISION_PACKAGE_BYTES=16+31*4 };
typedef struct {
    uint8_t y_offset, y_extent, x_offset, x_extent;
} YsPcCollisionBox;
typedef struct {
    YsPcCollisionBox boxes[YS_PC_COLLISION_BOXES];
} YsPcCollisionTable;
/* Values correspond to original bank4 $807C caller registers and
   IX+17 / IX+16, NOT invented native world/map coordinates. */
typedef struct {
    uint8_t origin_y,origin_x;
    uint8_t c,b,e,d;
} YsPcCollisionProbe;

bool ys_pc_collision_load(FILE *file,YsPcCollisionTable *out);
/* Returns false on bad arguments/index; on success, the carry output
   matches the original Z80 routine's RET carry flag. */
bool ys_pc_collision_eval(const YsPcCollisionTable *data,unsigned index,
                          const YsPcCollisionProbe *p,bool *carry);
#endif
