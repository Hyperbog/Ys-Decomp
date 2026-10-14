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
    YS_PC_COLLISION_ROUTE_BAD_INDEX,
    YS_PC_COLLISION_ROUTE_INACTIVE
} YsPcCollisionRouteStatus;

/* Original bank1 $4783-$479C / $48A5-$48BE derives target
   C/B/E/D from C20D or C20E and C211/C210 using 8-bit ADD.
   IX13/14 chooses the collision descriptor at each $807C caller;
   IX17/16 contains the origin of the tested object.
   No live gameplay values are inferred from these input names. */
typedef struct {
    uint8_t slot2_bank, c20d, c20e, c211, c210;
    uint8_t ix13, ix14, ix17, ix16;
} YsPcCollisionFrameInput;

/* Reproduce ORIGINAL bounds construction before the native $807C
   predicate. INACTIVE means original double-ADD returned early for
   selector 0 or 128. Invalid/unverified descriptor indices fail closed.
   This still does not model a game-map wall collision. */
YsPcCollisionRouteStatus ys_pc_collision_route_frame(
    const YsPcCollisionTable *table,YsPcCollisionRoute route,
    const YsPcCollisionFrameInput *frame,YsPcCollisionCallResult *out);

/* Execute ONLY the proven native object-boundary predicate with
   EXPLICIT mapper+IX/register inputs. Does not infer original gameplay
   entry at $476C, world coordinates, collision grid or player identity.
   out is unchanged on any failure. */
YsPcCollisionRouteStatus ys_pc_collision_route_eval(
    const YsPcCollisionTable *table,YsPcCollisionRoute route,
    const YsPcCollisionCallState *state,YsPcCollisionCallResult *out);

#endif
