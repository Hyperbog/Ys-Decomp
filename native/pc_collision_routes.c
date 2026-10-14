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

YsPcCollisionRouteStatus ys_pc_collision_route_frame(
    const YsPcCollisionTable *table,YsPcCollisionRoute route,
    const YsPcCollisionFrameInput *frame,YsPcCollisionCallResult *out) {
    if(!table || !frame || !out ||
       route<YS_PC_COLLISION_ROUTE_FORWARD ||
       route>YS_PC_COLLISION_ROUTE_ALTERNATE)
        return YS_PC_COLLISION_ROUTE_BAD_ARGUMENT;
    if(frame->slot2_bank!=4u)
        return YS_PC_COLLISION_ROUTE_WRONG_BANK;

    /* $4783/$48A5: ADD A,A; RET Z. A=$00 or $80 gives zero.
       Only the source-verified first 31 four-byte descriptor
       entries may become canonical native collision inputs. */
    unsigned selector=route==YS_PC_COLLISION_ROUTE_ALTERNATE ?
        frame->c20e:frame->c20d;
    if((selector&0x7Fu)==0u)
        return YS_PC_COLLISION_ROUTE_INACTIVE;
    if(selector>=YS_PC_COLLISION_BOXES)
        return YS_PC_COLLISION_ROUTE_BAD_INDEX;
    const YsPcCollisionBox *box=&table->boxes[selector];
    /* $478C-$479C, $48AE-$48BE: C and E add to the
       PREVIOUS 8-bit A, not independently to the base. */
    uint8_t b=(uint8_t)((unsigned)frame->c211+box->y_offset);
    uint8_t c=(uint8_t)((unsigned)b+box->y_extent);
    uint8_t d=(uint8_t)((unsigned)frame->c210+box->x_offset);
    uint8_t e=(uint8_t)((unsigned)d+box->x_extent);
    YsPcCollisionCallState input={
        frame->slot2_bank,frame->ix13,frame->ix14,
        {frame->ix17,frame->ix16,c,b,e,d}
    };
    return ys_pc_collision_route_eval(table,route,&input,out);
}
