#include "pc_records.h"
#include <string.h>

enum { HEADER=16, GROUP_BYTES=6,
       PAYLOAD=YS_PC_RECORD_FILE_BYTES-HEADER };
static uint16_t word(const uint8_t *p) {
    return (uint16_t)((unsigned)p[0]|((unsigned)p[1]<<8));
}
static uint32_t crc32_bytes(const uint8_t *data,size_t size) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<size;++i) {
        crc^=data[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u & (0u-(crc&1u)));
    }
    return ~crc;
}
unsigned ys_pc_records_start(const YsPcRecords *r,unsigned group) {
    if(!r || group>=YS_PC_GROUP_COUNT) return 0u;
    unsigned offset=0u;
    for(unsigned i=0;i<group;++i) offset+=r->groups[i].count;
    return offset;
}
bool ys_pc_records_load(FILE *file,YsPcRecords *out) {
    if(!file || !out) return false;
    uint8_t raw[YS_PC_RECORD_FILE_BYTES];
    static const uint8_t magic[8]={'Y','S','P','C','7','M','0','1'};
    if(fread(raw,1,sizeof(raw),file)!=sizeof(raw) || fgetc(file)!=EOF ||
       memcmp(raw,magic,8u)!=0 || word(raw+8)!=YS_PC_GROUP_COUNT ||
       word(raw+10)!=YS_PC_RECORD_COUNT)
        return false;
    uint32_t crc=(uint32_t)raw[12]|((uint32_t)raw[13]<<8)|
                 ((uint32_t)raw[14]<<16)|((uint32_t)raw[15]<<24);
    if(crc32_bytes(raw+HEADER,PAYLOAD)!=crc) return false;
    YsPcRecords temp;
    unsigned count=0u,terminators=0u;
    for(unsigned i=0;i<YS_PC_GROUP_COUNT;++i) {
        const uint8_t *p=raw+HEADER+i*GROUP_BYTES;
        unsigned addr=word(p),num=word(p+2u),term=p[4u];
        unsigned stop=(i+1u<YS_PC_GROUP_COUNT)?
            word(raw+HEADER+(i+1u)*GROUP_BYTES):0xBDBFu;
        if(addr<0xBA67u || addr>=0xBDBFu || stop<=addr ||
           stop>0xBDBFu || term>1u || p[5u]!=0u ||
           num>YS_PC_RECORD_COUNT-count ||
           addr+num*4u+term!=stop ||
           (i==0u && addr!=0xBA67u) ||
           (i==YS_PC_GROUP_COUNT-1u && addr!=0xBDBAu))
            return false;
        temp.groups[i].source_pc=(uint16_t)addr;
        temp.groups[i].count=(uint16_t)num;
        temp.groups[i].terminator_zero=term!=0u;
        count+=num;terminators+=term;
    }
    if(count!=YS_PC_RECORD_COUNT || terminators!=20u) return false;
    memcpy(temp.records,raw+HEADER+YS_PC_GROUP_COUNT*GROUP_BYTES,
           YS_PC_RECORD_COUNT*YS_PC_RECORD_WIDTH);
    memcpy(temp.staging,raw+HEADER+YS_PC_GROUP_COUNT*GROUP_BYTES+
           YS_PC_RECORD_COUNT*YS_PC_RECORD_WIDTH,YS_PC_STAGING_BYTES);
    *out=temp;
    return true;
}
