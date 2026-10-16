#include "pc_nametable.h"
#include <string.h>

static uint32_t crc32_bytes(const uint8_t *p,size_t length) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<length;++i) {
        crc^=p[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
bool ys_pc_nametable_load(FILE *file,YsPcNameTable *out) {
    static const uint8_t magic[8]={'Y','S','P','C','6','N','0','1'};
    uint8_t header[16];
    YsPcNameTable tmp;
    if(!file || !out ||
       fread(header,1,sizeof(header),file)!=sizeof(header) ||
       memcmp(header,magic,sizeof(magic))!=0 ||
       header[8]!=0u || header[9]!=0x39u ||
       header[10]!=0u || header[11]!=6u ||
       fread(tmp.raw,1,sizeof(tmp.raw),file)!=sizeof(tmp.raw) ||
       fgetc(file)!=EOF) return false;
    uint32_t expected=(uint32_t)header[12]|
        ((uint32_t)header[13]<<8)|((uint32_t)header[14]<<16)|
        ((uint32_t)header[15]<<24);
    if(crc32_bytes(tmp.raw,sizeof(tmp.raw))!=expected) return false;
    *out=tmp;
    return true;
}
bool ys_pc_nametable_cell(const YsPcNameTable *table,
                          unsigned col,unsigned row,YsPcNameCell *out) {
    if(!table || !out || col>=YS_PC_NT_W || row>=YS_PC_NT_H)
        return false;
    size_t offset=((size_t)row*YS_PC_NT_W+col)*2u;
    uint16_t word=(uint16_t)((unsigned)table->raw[offset]|
                   ((unsigned)table->raw[offset+1u]<<8u));
    YsPcNameCell cell={
        (uint16_t)(word&0x01FFu),word,
        (word&0x0200u)!=0u,(word&0x0400u)!=0u,
        (word&0x0800u)!=0u,(word&0x1000u)!=0u
    };
    *out=cell;
    return true;
}
