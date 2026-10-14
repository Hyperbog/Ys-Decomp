#include "pc_objects.h"
#include <string.h>

static void put(YsPcObjectSlot *slot,unsigned offset,uint8_t value) {
    slot->work[offset]=value;
    slot->known[offset]=1u;
}
static void put16(YsPcObjectSlot *slot,unsigned offset,uint16_t value) {
    put(slot,offset,(uint8_t)value);
    put(slot,offset+1u,(uint8_t)(value>>8));
}
bool ys_pc_project_objects(const YsPcRecords *data,unsigned group,
                           YsPcObjectProjection *out) {
    if(!data || !out || group>=YS_PC_GROUP_COUNT) return false;
    unsigned count=data->groups[group].count;
    unsigned begin=ys_pc_records_start(data,group);
    if(count>YS_PC_OBJECT_SLOTS || begin>YS_PC_RECORD_COUNT ||
       count>YS_PC_RECORD_COUNT-begin) return false;
    YsPcObjectProjection result={0};
    result.group=group;
    result.count=count;
    for(unsigned i=0;i<count;++i) {
        const uint8_t *src=data->records[begin+i];
        if(src[0]==0u) return false; /* Original source stops at first zero. */
        YsPcObjectSlot *slot=&result.objects[i];
        slot->source_record_pc=(uint16_t)(
            data->groups[group].source_pc+i*YS_PC_RECORD_WIDTH);
        memcpy(slot->source,src,4u);
        /* Exact arithmetic from source $1B66-$1B8E:
           HL=source[2]*8+8; then HL=source[3]*8.
           The (IX+d),L/H store opcodes use actual H/L as the source
           because indexed-memory forms are the Z80 documented exception
           to ordinary DD prefix H/L -> IXH/IXL substitution. */
        slot->value_a=(uint16_t)((unsigned)src[2]*8u+8u);
        slot->value_b=(uint16_t)((unsigned)src[3]*8u);
        put(slot,0u,src[0]);
        put(slot,41u,src[0]);
        put(slot,32u,src[1]);
        put16(slot,6u,slot->value_a);
        put16(slot,43u,slot->value_a);
        put16(slot,3u,slot->value_b);
        put16(slot,45u,slot->value_b);
    }
    *out=result;
    return true;
}
