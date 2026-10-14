#ifndef YS_PC_COLLISION_ROUTES_H
#define YS_PC_COLLISION_ROUTES_H

#include <stdbool.h>
#include <stdint.h>
#include "pc_collision.h"

/* Stable NATIVE symbolic cases for three original bank1 predicate callers.
   The source CPU addresses are provenance, not public mod identities. */
typedef enum {
    YS_PC_COLLISION_ROUTE_FORWARD = 0, /* source $47C2, IX+14 */
    YS_PC_COLLISION_ROUTE_CONTACT = 1, /* source $486C, IX+14 */
    YS_PC_COLLISION_ROUTE_ALTERNATE = 2 /* source $48DF, IX+13 */
} YsPcCollisionRoute;

typedef struct {
    uint8_t slot2_bank; /* Explicit active mapper value, never guessed. */
    uint8_t ix13,ix14;  /* Original object-work descriptor indices. */
    YsPcCollisionProbe probe; /* IX+17/+16 and incoming C/B/E/D. */
} YsPcCollisionCallState;

typedef struct {
    uint16_t original_source_pc; /* Diagnostic provenance only. */
    uint8_t descriptor_index;    /* Original bank4 31-record index. */
    bool carry;                  /* Original $807C predicate result. */
} YsPcCollisionCallResult;

typedef enum {
    YS_PC_COLLISION_ROUTE_OK=0,
    YS_PC_COLLISION_ROUTE_BAD_ARGUMENT,
    YS_PC_COLLISION_ROUTE_WRONG_BANK,
    YS_PC_COLLISION_ROUTE_BAD_INDEX
} YsPcCollisionRouteStatus;

/* Execute ONLY the proven native object-boundary predicate with
   EXPLICIT mapper+IX/register inputs. Does not infer original gameplay
   entry at $476C, world coordinates, collision grid or player identity.
   out is unchanged on any failure. */
YsPcCollisionRouteStatus ys_pc_collision_route_eval(
    const YsPcCollisionTable *table,YsPcCollisionRoute route,
    const YsPcCollisionCallState *state,YsPcCollisionCallResult *out);

#endif
