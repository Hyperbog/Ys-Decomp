#include "pc_scenes.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static const uint16_t targets[9]={
    0x2C36u,0x2D9Du,0x2F2Au,0x3014u,0x3194u,
    0x329Cu,0x333Bu,0x3415u,0x3519u
};
static uint32_t crc32_bytes(const uint8_t *raw,unsigned count) {
    uint32_t crc=0xFFFFFFFFu;
    for(unsigned i=0;i<count;++i) {
        crc^=raw[i];
        for(unsigned b=0;b<8u;++b)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
static void put16(uint8_t *raw,unsigned offset,unsigned value) {
    raw[offset]=(uint8_t)value;
    raw[offset+1]=(uint8_t)(value>>8);
}
static void fix_crc(uint8_t *raw) {
    uint32_t crc=crc32_bytes(raw+16u,34u);
    for(unsigned k=0;k<4u;++k)
        raw[12u+k]=(uint8_t)(crc>>(8u*k));
}
static void fixture(uint8_t raw[YS_PC_SCENE_FILE_BYTES]) {
    memset(raw,0,YS_PC_SCENE_FILE_BYTES);
    memcpy(raw,"YSPC5S01",8u);
    put16(raw,8u,9u);
    put16(raw,10u,8u);
    for(unsigned i=0;i<9u;++i) put16(raw,16u+i*2u,targets[i]);
    for(unsigned i=0;i<8u;++i)
        put16(raw,34u+i*2u,i<4u?0x4C13u:0x4C26u);
    fix_crc(raw);
}
static bool from_bytes(const uint8_t *raw,size_t size,
                       YsPcSceneDirectory *out) {
    FILE *f=tmpfile();
    assert(f);
    assert(fwrite(raw,1,size,f)==size);
    rewind(f);
    bool result=ys_pc_scenes_load(f,out);
    fclose(f);
    return result;
}
static void verify_selection(const YsPcSceneDirectory *source) {
    YsPcSceneSelection result;
    assert(!ys_pc_scene_select(NULL,0u,0u,&result));
    assert(!ys_pc_scene_select(source,0u,0u,NULL));
    assert(!ys_pc_scene_select(source,9u,0u,&result));
    assert(ys_pc_scene_select(source,0u,0u,&result));
    assert(result.scene_handler==targets[0] && result.has_group &&
           result.object_group==0u && !result.c181_high_bit);
    assert(ys_pc_scene_select(source,8u,0x95u,&result));
    assert(result.scene_handler==targets[8] && result.has_group &&
           result.object_group==21u && result.c181_high_bit &&
           result.c181==0x95u && result.c119==8u);
    assert(ys_pc_scene_select(source,8u,0x96u,&result));
    assert(result.object_group==22u && !result.has_group);
    assert(ys_pc_scene_select(source,8u,0xFFu,&result));
    assert(result.object_group==127u && !result.has_group &&
           result.c181_high_bit);
}
static void test_fixture(void) {
    uint8_t raw[YS_PC_SCENE_FILE_BYTES];
    YsPcSceneDirectory scene;
    fixture(raw);
    assert(!ys_pc_scenes_load(NULL,&scene));
    assert(from_bytes(raw,sizeof(raw),&scene));
    for(unsigned i=0;i<9u;++i)
        assert(scene.fixed_handlers[i]==targets[i]);
    assert(scene.bank1_entries[0]==0x4C13u &&
           scene.bank1_entries[7]==0x4C26u);
    verify_selection(&scene);
    assert(!from_bytes(raw,sizeof(raw)-1u,&scene));
    raw[0]='?';assert(!from_bytes(raw,sizeof(raw),&scene));
    fixture(raw);raw[20u]^=1u;
    assert(!from_bytes(raw,sizeof(raw),&scene));
    fixture(raw);put16(raw,8u,8u);fix_crc(raw);
    assert(!from_bytes(raw,sizeof(raw),&scene));
    fixture(raw);put16(raw,16u+4u*2u,targets[3]);fix_crc(raw);
    assert(!from_bytes(raw,sizeof(raw),&scene)); /* duplicate handler */
    fixture(raw);put16(raw,34u,0x3FFFu);fix_crc(raw);
    assert(!from_bytes(raw,sizeof(raw),&scene)); /* wrong bank1 */
}
static void source_asset(const char *path) {
    FILE *f=fopen(path,"rb");
    assert(f);
    YsPcSceneDirectory scene;
    assert(ys_pc_scenes_load(f,&scene));
    fclose(f);
    for(unsigned i=0;i<9u;++i)
        assert(scene.fixed_handlers[i]==targets[i]);
    for(unsigned i=0;i<8u;++i)
        assert(scene.bank1_entries[i]>=0x4C13u &&
               scene.bank1_entries[i]<0x4C80u);
    verify_selection(&scene);
    puts("PASS PC-5 actual source-derived 9+8 dispatcher pointers");
}
int main(int argc,char **argv) {
    assert(argc==1 || argc==2);
    test_fixture();
    if(argc==2) source_asset(argv[1]);
    puts("PASS PC-5 independent scene/object selectors; invalid indices, CRC and source bounds");
    return 0;
}
