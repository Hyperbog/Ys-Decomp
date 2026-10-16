#include "pc_collision.h"
#include <string.h>

static uint32_t crc32_bytes(const uint8_t *bytes,size_t len) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<len;++i) {
        crc^=bytes[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
bool ys_pc_collision_load(FILE *file,YsPcCollisionTable *out) {
    uint8_t header[16],raw[YS_PC_COLLISION_BOXES*YS_PC_COLLISION_STRIDE];
    static const uint8_t magic[8]={'Y','S','P','C','9','C','0','1'};
    if(!file || !out ||
       fread(header,1,sizeof(header),file)!=sizeof(header) ||
       memcmp(header,magic,sizeof(magic))!=0 ||
       header[8]!=YS_PC_COLLISION_BOXES || header[9]!=0u ||
       header[10]!=YS_PC_COLLISION_STRIDE || header[11]!=0u ||
       fread(raw,1,sizeof(raw),file)!=sizeof(raw) ||
       fgetc(file)!=EOF) return false;
    uint32_t crc=(uint32_t)header[12]|
        ((uint32_t)header[13]<<8u)|
        ((uint32_t)header[14]<<16u)|
        ((uint32_t)header[15]<<24u);
    if(crc!=crc32_bytes(raw,sizeof(raw))) return false;
    YsPcCollisionTable temp;
    for(unsigned i=0;i<YS_PC_COLLISION_BOXES;++i) {
        const uint8_t *p=raw+i*YS_PC_COLLISION_STRIDE;
        temp.boxes[i]=(YsPcCollisionBox){p[0],p[1],p[2],p[3]};
    }
    *out=temp;
    return true;
}
/* Direct field-arithmetic equivalent of the bounded original Z80
   $807C-$80A1 predicate (ADD with IX origins, RET NC, CP and JR).
   Unsigned additions MUST preserve the original carry/overflow tests.
   Never treat this as a tilemap wall-collision test without evidence. */
bool ys_pc_collision_eval(const YsPcCollisionTable *data,unsigned index,
                          const YsPcCollisionProbe *p,bool *carry) {
    if(!data || !p || !carry || index>=YS_PC_COLLISION_BOXES)
        return false;
    const YsPcCollisionBox *box=&data->boxes[index];
    unsigned yy=(unsigned)box->y_offset+p->origin_y;
    bool hit=false;
    if(yy>=256u) {
        unsigned y=yy&255u;
        bool y_ok=(y==p->c);
        if(!y_ok && y<p->c) {
            unsigned end_y=y+box->y_extent;
            y_ok=end_y<256u && end_y>=p->b;
        }
        if(y_ok) {
            unsigned xx=(unsigned)box->x_offset+p->origin_x;
            if(xx>=256u) {
                unsigned x=xx&255u;
                if(x==p->e)
                    hit=true;
                else if(x<p->e) {
                    unsigned end_x=x+box->x_extent;
                    hit=end_x<256u && end_x>=p->d;
                }
            }
        }
    }
    *carry=hit;
    return true;
}
