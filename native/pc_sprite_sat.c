#include "pc_sprite_sat.h"
#include <string.h>

static unsigned le16(const uint8_t *p) {
    return (unsigned)p[0]|((unsigned)p[1]<<8u);
}
static unsigned long crc32(const uint8_t *bytes,size_t len) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<len;++i) {
        crc^=bytes[i];
        for(unsigned bit=0;bit<8u;++bit)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return (unsigned long)(~crc);
}
bool ys_pc_sprite_records_load(FILE *file,YsPcSpriteRecords *out) {
    if(!file || !out) return false;
    uint8_t header[16],raw[YS_PC_SPRITE_POINTER_BYTES+
                           YS_PC_SPRITE_STREAM_BYTES];
    static const uint8_t magic[8]={'Y','S','P','C','1','4','S','1'};
    if(fread(header,1u,sizeof(header),file)!=sizeof(header) ||
       memcmp(header,magic,sizeof(magic))!=0 ||
       le16(header+8u)!=YS_PC_SPRITE_RECORDS ||
       le16(header+10u)!=sizeof(raw) ||
       fread(raw,1u,sizeof(raw),file)!=sizeof(raw) ||
       fgetc(file)!=EOF)
        return false;
    uint32_t wanted=(uint32_t)header[12] |
        ((uint32_t)header[13]<<8u) |
        ((uint32_t)header[14]<<16u) |
        ((uint32_t)header[15]<<24u);
    if((uint32_t)crc32(raw,sizeof(raw))!=wanted) return false;
    /* Pointer addresses must describe exactly one contiguous stream
       partition (directory order need not match source CPU order). */
    uint8_t covered[YS_PC_SPRITE_STREAM_BYTES]={0};
    YsPcSpriteRecords value={0};
    memcpy(value.stream,raw+YS_PC_SPRITE_POINTER_BYTES,
           YS_PC_SPRITE_STREAM_BYTES);
    unsigned counted=0;
    for(unsigned i=0;i<YS_PC_SPRITE_RECORDS;++i) {
        unsigned p=le16(raw+i*2u);
        if(p<0x8080u || p>=0x9932u) return false;
        unsigned start=p-0x8080u;
        unsigned count=value.stream[start];
        if(count==0u || count>64u ||
           start+1u+3u*count>YS_PC_SPRITE_STREAM_BYTES)
            return false;
        unsigned size=1u+3u*count;
        for(unsigned j=0;j<size;++j) {
            if(covered[start+j]) return false;
            covered[start+j]=1u;
        }
        counted+=size;
        value.pointers[i]=(uint16_t)p;
    }
    if(counted!=YS_PC_SPRITE_STREAM_BYTES) return false;
    *out=value; /* Only commit on full source-structure verification. */
    return true;
}
bool ys_pc_sprite_stage(const YsPcSpriteRecords *records,unsigned index,
                        uint8_t origin_y,uint8_t origin_x,
                        YsPcSatBuffer *out) {
    if(!records || !out || index>=YS_PC_SPRITE_RECORDS) return false;
    unsigned p=records->pointers[index];
    if(p<0x8080u || p>=0x9932u) return false;
    unsigned offset=p-0x8080u;
    unsigned count=records->stream[offset];
    if(count==0u || count>=YS_PC_SAT_Y_BYTES ||
       offset+1u+3u*count>YS_PC_SPRITE_STREAM_BYTES) return false;
    YsPcSatBuffer result;
    memset(result.y,0xD0,sizeof(result.y));
    memset(result.xt,0,sizeof(result.xt));
    result.count=(uint8_t)count;
    uint8_t y=origin_y;
    uint8_t x=origin_x;
    for(unsigned i=0;i<count;++i) {
        y=(uint8_t)(y+records->stream[offset+1u+i]);
        result.y[i]=y;
    }
    for(unsigned i=0;i<count;++i) {
        x=(uint8_t)(x+records->stream[offset+1u+count+2u*i]);
        result.xt[2u*i]=x;
        result.xt[2u*i+1u]=records->stream[offset+2u+count+2u*i];
    }
    *out=result;
    return true;
}
