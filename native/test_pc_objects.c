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
    r->groups[1].source_pc=0xBA6Fu;
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
/* Optional *real source-derived* group-data verification. This is
   not a RAM execution trace or an authenticated scene placement. */
static void verify_source_package(const char *path,const char *type_path) {
    FILE *f=fopen(path,"rb");
    assert(f);
    YsPcRecords recovered;
    assert(ys_pc_records_load(f,&recovered));
    fclose(f);
    YsPcObjectTypes table;
    if(type_path) {
        FILE *source=fopen(type_path,"rb");
        assert(source);
        assert(ys_pc_object_types_load(source,&table));
        fclose(source);
    }
    YsPcObjectProjection projection;
    unsigned total=0u,zero_groups=0u,defaults=0u,indexed=0u;
    unsigned seen[YS_PC_OBJECT_TYPE_COUNT]={0};
    for(unsigned g=0u;g<YS_PC_GROUP_COUNT;++g) {
        assert(type_path ?
               ys_pc_project_objects_typed(&recovered,g,&table,&projection) :
               ys_pc_project_objects(&recovered,g,&projection));
        assert(projection.count==recovered.groups[g].count);
        total+=projection.count;
        if(!projection.count) ++zero_groups;
        for(unsigned i=0u;i<projection.count;++i) {
            const YsPcObjectSlot *p=&projection.objects[i];
            assert(p->source_record_pc==
                   recovered.groups[g].source_pc+4u*i);
            assert(p->value_a==(unsigned)p->source[2]*8u+8u);
            assert(p->value_b==(unsigned)p->source[3]*8u);
            assert(p->work[0]==p->source[0] &&
                   p->work[41]==p->source[0] &&
                   p->work[32]==p->source[1]);
            if(!type_path) verify_known_bytes(p);
            else if((p->source[1]&0x80u)==0u) {
                ++defaults;
                assert(p->work[1]==0x20u && p->work[18]==1u &&
                       p->work[33]==4u && p->work[13]==10u &&
                       p->work[14]==10u && !p->known[34]);
            } else {
                ++indexed;
                unsigned index=p->source[1]&0x7Fu;
                assert(index<YS_PC_OBJECT_TYPE_COUNT);
                ++seen[index];
                const uint8_t *entry=table.entry[index];
                assert(p->work[33]==entry[0] && p->work[34]==entry[1] &&
                       p->work[42]==entry[1]);
                for(unsigned v=0u;v<6u;++v)
                    assert(p->known[35u+v] &&
                           p->work[35u+v]==entry[2u+v]);
                assert(p->work[23]==entry[8] && p->work[24]==entry[9] &&
                       p->work[18]==1u && p->work[1]==0x20u &&
                       p->work[14]==1u && !p->known[13u]);
            }
        }
    }
    assert(total==209u && zero_groups==1u);
    if(type_path) {
        assert(defaults==36u && indexed==173u);
        for(unsigned i=0;i<YS_PC_OBJECT_TYPE_COUNT;++i)
            assert(seen[i]!=0u);
    }
    assert(type_path ?
           ys_pc_project_objects_typed(&recovered,0u,&table,&projection) :
           ys_pc_project_objects(&recovered,0u,&projection));
    assert(projection.count==16u);
    assert(projection.objects[0].source[0]==3u);
    assert(projection.objects[0].source[1]==0u);
    assert(projection.objects[0].value_a==56u);
    assert(projection.objects[0].value_b==352u);
    puts(type_path ?
        "PASS PC-4: 36 default, 173 indexed source objects; 35 table entries used" :
        "PASS PC-3: all 209 source-derived bank7 object fields projected");
}
int main(int argc,char **argv) {
    assert(argc>=1 && argc<=3);
    if(argc>=2) verify_source_package(argv[1],argc==3?argv[2]:NULL);
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
