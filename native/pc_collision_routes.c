#include "pc_collision_routes.h"

YsPcCollisionRouteStatus ys_pc_collision_route_eval(
    const YsPcCollisionTable *table,YsPcCollisionRoute route,
    const YsPcCollisionCallState *state,YsPcCollisionCallResult *out) {
    if(!table || !state || !out ||
       route<YS_PC_COLLISION_ROUTE_FORWARD ||
       route>YS_PC_COLLISION_ROUTE_ALTERNATE)
        return YS_PC_COLLISION_ROUTE_BAD_ARGUMENT;
    /* Source bank1 $4771-$4775 maps physical bank 4 before each
       reachable call on the $476C entry path. Other entries, and the
       mapper state of an actual gameplay invocation, remain unknown. */
    if(state->slot2_bank!=4u)
        return YS_PC_COLLISION_ROUTE_WRONG_BANK;

    const unsigned ixoff=route==YS_PC_COLLISION_ROUTE_ALTERNATE?13u:14u;
    const unsigned index=ixoff==13u?state->ix13:state->ix14;
    if(index>=YS_PC_COLLISION_BOXES)
        return YS_PC_COLLISION_ROUTE_BAD_INDEX;
    bool carry=false;
    if(!ys_pc_collision_eval(table,index,&state->probe,&carry))
        return YS_PC_COLLISION_ROUTE_BAD_ARGUMENT;
    static const uint16_t source_pc[3]={0x47C2u,0x486Cu,0x48DFu};
    YsPcCollisionCallResult result={(uint16_t)source_pc[(unsigned)route],
                                     (uint8_t)index,carry};
    *out=result;
    return YS_PC_COLLISION_ROUTE_OK;
}
