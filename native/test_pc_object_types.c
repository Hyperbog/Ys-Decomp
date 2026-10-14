#include "pc_objects.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t checksum(const uint8_t *bytes,unsigned count) {
    uint32_t crc=0xFFFFFFFFu;
    for(unsigned i=0;i<count;++i) {
        crc^=bytes[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
static void header_crc(uint8_t raw[YS_PC_OBJECT_TYPE_FILE_BYTES]) {
    uint32_t crc=checksum(raw+16u,350u);
    for(unsigned j=0;j<4u;++j) raw[12u+j]=(uint8_t)(crc>>(8u*j));
}
static bool load_fixture(const uint8_t *raw,unsigned size,YsPcObjectTypes *out) {
    FILE *f=tmpfile();
    assert(f);
    assert(fwrite(raw,1,size,f)==size);
    rewind(f);
    bool valid=ys_pc_object_types_load(f,out);
    fclose(f);
    return valid;
}
static void build_fixture(uint8_t raw[YS_PC_OBJECT_TYPE_FILE_BYTES]) {
    memset(raw,0,YS_PC_OBJECT_TYPE_FILE_BYTES);
    memcpy(raw,"YSPC4O01",8u);
    raw[8]=35u;raw[10]=10u;
    for(unsigned i=0;i<35u;++i)
        for(unsigned j=0;j<10u;++j)
            raw[16u+i*10u+j]=(uint8_t)(i*7u+j);
    header_crc(raw);
}
static void test_loader(void) {
    uint8_t raw[YS_PC_OBJECT_TYPE_FILE_BYTES];
    YsPcObjectTypes table;
    build_fixture(raw);
    assert(ys_pc_object_types_load(NULL,&table)==false);
    assert(load_fixture(raw,sizeof(raw),&table));
    assert(table.entry[0][0]==0u && table.entry[34][9]==247u);
    assert(!load_fixture(raw,sizeof(raw)-1u,&table));
    raw[0]='X';assert(!load_fixture(raw,sizeof(raw),&table));
    build_fixture(raw);
    raw[20u]^=1u;assert(!load_fixture(raw,sizeof(raw),&table));
    build_fixture(raw);
    raw[8]=34u;header_crc(raw);
    assert(!load_fixture(raw,sizeof(raw),&table));
    build_fixture(raw);
    raw[10]=9u;header_crc(raw);
    assert(!load_fixture(raw,sizeof(raw),&table));
}
static void verify_exact_mask(const YsPcObjectSlot *slot,bool indexed) {
    bool want[YS_PC_OBJECT_SLOT_BYTES]={0};
    const unsigned common[]={0u,3u,4u,6u,7u,32u,41u,43u,44u,45u,46u};
    const unsigned low[]={1u,13u,14u,18u,33u};
    const unsigned high[]={1u,14u,18u,23u,24u,33u,34u,42u};
    for(unsigned i=0;i<sizeof(common)/sizeof(common[0]);++i)
        want[common[i]]=true;
    if(indexed) {
        for(unsigned i=0;i<sizeof(high)/sizeof(high[0]);++i)
            want[high[i]]=true;
        for(unsigned i=35u;i<=40u;++i) want[i]=true;
    } else
        for(unsigned i=0;i<sizeof(low)/sizeof(low[0]);++i)
            want[low[i]]=true;
    for(unsigned i=0;i<YS_PC_OBJECT_SLOT_BYTES;++i)
        assert((slot->known[i]!=0u)==want[i]);
}
static void test_init_paths(void) {
    uint8_t raw[YS_PC_OBJECT_TYPE_FILE_BYTES];
    YsPcObjectTypes table;
    build_fixture(raw);
    assert(load_fixture(raw,sizeof(raw),&table));
    YsPcRecords src={0};
    src.groups[0].source_pc=0xBA67u;
    src.groups[0].count=2u;
    src.records[0][0]=3u;
    src.records[0][1]=0x81u; /* type index 1; high branch. */
    src.records[0][2]=6u;src.records[0][3]=44u;
    src.records[1][0]=5u;
    src.records[1][1]=0x01u; /* low branch. */
    YsPcObjectProjection out={0};
    assert(ys_pc_project_objects_typed(&src,0u,&table,&out));
    const YsPcObjectSlot *hi=&out.objects[0];
    const YsPcObjectSlot *lo=&out.objects[1];
    verify_exact_mask(hi,true);
    verify_exact_mask(lo,false);
    assert(hi->work[0]==3u && hi->work[32]==0x81u);
    assert(hi->value_a==56u && hi->value_b==352u);
    assert(hi->work[33]==table.entry[1][0]);
    assert(hi->work[34]==table.entry[1][1] &&
           hi->work[42]==table.entry[1][1]);
    for(unsigned i=0;i<6u;++i)
        assert(hi->known[35u+i] && hi->work[35u+i]==table.entry[1][2u+i]);
    assert(hi->work[23]==table.entry[1][8] &&
           hi->work[24]==table.entry[1][9]);
    assert(hi->work[1]==0x20u && hi->work[18]==1u &&
           hi->work[14]==1u && !hi->known[13]);
    assert(lo->work[1]==0x20u && lo->work[33]==4u &&
           lo->work[18]==1u && lo->work[13]==10u &&
           lo->work[14]==10u);
    assert(!lo->known[34] && !lo->known[42] && !lo->known[23]);
    /* Legacy PC-3 path deliberately has only 11 known source bytes. */
    assert(ys_pc_project_objects(&src,0u,&out));
    assert(!out.objects[0].known[33] && !out.objects[1].known[13]);
    src.records[0][1]=0xA2u; /* highest legal index 34. */
    assert(ys_pc_project_objects_typed(&src,0u,&table,&out));
    assert(out.objects[0].work[33]==table.entry[34][0]);
    src.records[0][1]=0xA3u; /* 35 exceeds table. */
    assert(!ys_pc_project_objects_typed(&src,0u,&table,&out));
    src.records[0][1]=0xFFu;
    assert(!ys_pc_project_objects_typed(&src,0u,&table,&out));
    assert(!ys_pc_project_objects_typed(NULL,0u,&table,&out));
    assert(!ys_pc_project_objects_typed(&src,22u,&table,&out));
}
int main(void) {
    test_loader();
    test_init_paths();
    puts("PASS PC-4: 35x10 source table, CRC/count rejection, default and indexed $1B9B writes");
    return 0;
}
