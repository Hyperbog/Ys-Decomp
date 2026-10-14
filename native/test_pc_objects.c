#include "pc_objects.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void fixture(YsPcRecords *r) {
    memset(r,0,sizeof(*r));
    r->groups[0].source_pc=0xBA67u;
    r->groups[0].count=2u;
    r->records[0][0]=3u;r->records[0][1]=0x81u;
    r->records[0][2]=6u;r->records[0][3]=44u;
    r->records[1][0]=0x82u;r->records[1][1]=0x01u;
    r->records[1][2]=255u;r->records[1][3]=255u;
    r->groups[1].source_pc=0xBA70u;
}
static void verify_known_bytes(const YsPcObjectSlot *s) {
    static const unsigned offsets[]={0,3,4,6,7,32,41,43,44,45,46};
    for(unsigned i=0;i<YS_PC_OBJECT_SLOT_BYTES;++i) {
        bool expected=false;
        for(unsigned j=0;j<sizeof(offsets)/sizeof(offsets[0]);++j)
            if(i==offsets[j]) expected=true;
        assert((s->known[i]!=0u)==expected);
    }
}
int main(void) {
    YsPcRecords records;
    YsPcObjectProjection out;
    fixture(&records);
    assert(!ys_pc_project_objects(NULL,0u,&out));
    assert(!ys_pc_project_objects(&records,22u,&out));
    assert(!ys_pc_project_objects(&records,0u,NULL));
    assert(ys_pc_project_objects(&records,0u,&out));
    assert(out.count==2u && out.group==0u);
    const YsPcObjectSlot *first=&out.objects[0];
    assert(first->source_record_pc==0xBA67u);
    assert(first->value_a==56u && first->value_b==352u);
    assert(first->work[0]==3u && first->work[41]==3u);
    assert(first->work[32]==0x81u);
    assert(first->work[6]==56u && first->work[7]==0u);
    assert(first->work[43]==56u && first->work[44]==0u);
    assert(first->work[3]==96u && first->work[4]==1u);
    assert(first->work[45]==96u && first->work[46]==1u);
    verify_known_bytes(first);
    const YsPcObjectSlot *second=&out.objects[1];
    assert(second->source_record_pc==0xBA6Bu);
    assert(second->source[0]==0x82u);
    assert(second->value_a==2048u && second->value_b==2040u);
    assert(second->work[6]==0u && second->work[7]==8u);
    assert(second->work[3]==248u && second->work[4]==7u);
    verify_known_bytes(second);
    assert(!out.objects[2].known[0]);
    /* Original group 4 is empty and has no simulated actor. */
    assert(ys_pc_project_objects(&records,4u,&out) && out.count==0u);
    /* Reject active zero records instead of inventing object state. */
    records.records[0][0]=0u;
    assert(!ys_pc_project_objects(&records,0u,&out));
    records.records[0][0]=3u;
    records.groups[0].count=17u;
    assert(!ys_pc_project_objects(&records,0u,&out));
    puts("PASS PC-3 bank0 source object fields: slot stride $30, 8x scaling, known-byte mask, high-bit and zero/overflow rejection");
    return 0;
}
