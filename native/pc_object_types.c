#include "pc_object_types.h"
#include <string.h>

static uint32_t crc32_bytes(const uint8_t *p,unsigned size) {
    uint32_t crc=0xFFFFFFFFu;
    for(unsigned i=0;i<size;++i) {
        crc^=p[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
bool ys_pc_object_types_load(FILE *file,YsPcObjectTypes *out) {
    static const uint8_t magic[8]={'Y','S','P','C','4','O','0','1'};
    uint8_t raw[YS_PC_OBJECT_TYPE_FILE_BYTES];
    if(!file || !out ||
       fread(raw,1,sizeof(raw),file)!=sizeof(raw) ||
       fgetc(file)!=EOF || memcmp(raw,magic,sizeof(magic))!=0 ||
       raw[8]!=35u || raw[9]!=0u || raw[10]!=10u || raw[11]!=0u)
        return false;
    uint32_t want=(uint32_t)raw[12]|
        ((uint32_t)raw[13]<<8)|((uint32_t)raw[14]<<16)|
        ((uint32_t)raw[15]<<24);
    if(want!=crc32_bytes(raw+16u,350u)) return false;
    YsPcObjectTypes temp;
    memcpy(temp.entry,raw+16u,350u);
    *out=temp;
    return true;
}
