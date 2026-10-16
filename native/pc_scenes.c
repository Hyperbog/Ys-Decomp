#include "pc_scenes.h"
#include <string.h>

static uint16_t read16(const uint8_t *s) {
    return (uint16_t)((unsigned)s[0]|((unsigned)s[1]<<8));
}
static uint32_t crc32_bytes(const uint8_t *buf,size_t size) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<size;++i) {
        crc^=buf[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
bool ys_pc_scenes_load(FILE *file,YsPcSceneDirectory *out) {
    static const uint8_t magic[8]={'Y','S','P','C','5','S','0','1'};
    uint8_t bytes[YS_PC_SCENE_FILE_BYTES];
    if(!file || !out ||
       fread(bytes,1,sizeof(bytes),file)!=sizeof(bytes) ||
       fgetc(file)!=EOF ||
       memcmp(bytes,magic,8u)!=0 ||
       read16(bytes+8u)!=YS_PC_SCENE_DISPATCH_COUNT ||
       read16(bytes+10u)!=YS_PC_BANK1_SCENE_ENTRY_COUNT)
        return false;
    uint32_t expected=(uint32_t)bytes[12] |
        ((uint32_t)bytes[13]<<8) |
        ((uint32_t)bytes[14]<<16) |
        ((uint32_t)bytes[15]<<24);
    if(crc32_bytes(bytes+16u,sizeof(bytes)-16u)!=expected)
        return false;
    YsPcSceneDirectory tmp;
    for(unsigned i=0;i<YS_PC_SCENE_DISPATCH_COUNT;++i) {
        unsigned target=read16(bytes+16u+2u*i);
        if(target<0x2C36u || target>=0x4000u ||
           (i && target<=tmp.fixed_handlers[i-1u]))
            return false;
        tmp.fixed_handlers[i]=(uint16_t)target;
    }
    for(unsigned i=0;i<YS_PC_BANK1_SCENE_ENTRY_COUNT;++i) {
        unsigned target=read16(bytes+16u+18u+2u*i);
        if(target<0x4C13u || target>=0x4C80u) return false;
        tmp.bank1_entries[i]=(uint16_t)target;
    }
    *out=tmp;
    return true;
}
bool ys_pc_scene_select(const YsPcSceneDirectory *source,
                        uint8_t c119,uint8_t c181,YsPcSceneSelection *out) {
    if(!source || !out || c119>=YS_PC_SCENE_DISPATCH_COUNT)
        return false;
    YsPcSceneSelection temp={0};
    temp.c119=c119;temp.c181=c181;
    temp.c181_high_bit=(uint8_t)((c181&0x80u)!=0u);
    temp.scene_handler=source->fixed_handlers[c119];
    temp.object_group=(unsigned)(c181&0x7Fu);
    temp.has_group=temp.object_group<22u;
    *out=temp;
    return true;
}
