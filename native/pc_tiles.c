#include "pc_tiles.h"
#include <string.h>

/* Standard IEEE CRC-32 for the derived, untracked tile package. */
static uint32_t crc32_bytes(const uint8_t *bytes,unsigned size) {
    uint32_t crc=0xFFFFFFFFu;
    for(unsigned i=0;i<size;++i) {
        crc^=bytes[i];
        for(unsigned j=0;j<8u;++j)
            crc=(crc>>1)^(0xEDB88320u & (0u-(crc&1u)));
    }
    return ~crc;
}
bool ys_pc_tiles_decode(const uint8_t *src,unsigned length,YsPcTiles *out) {
    if(!src || !out || length!=YS_PC_TILE_COUNT*YS_PC_TILE_BYTES)
        return false;
    YsPcTiles temp;
    for(unsigned t=0;t<YS_PC_TILE_COUNT;++t)
        for(unsigned y=0;y<8u;++y)
            for(unsigned x=0;x<8u;++x) {
                unsigned idx=0u;
                for(unsigned plane=0;plane<4u;++plane)
                    idx|=((src[t*32u+y*4u+plane]>>(7u-x))&1u)<<plane;
                temp.index[t][y*8u+x]=(uint8_t)idx;
            }
    *out=temp;
    return true;
}
bool ys_pc_tiles_load(FILE *fp,YsPcTiles *out) {
    if(!fp || !out) return false;
    uint8_t header[YS_PC_TILE_FILE_HEADER],raw[YS_PC_TILE_COUNT*YS_PC_TILE_BYTES];
    static const uint8_t magic[8]={'Y','S','P','C','4','T','0','1'};
    if(fread(header,1,sizeof(header),fp)!=sizeof(header) ||
       memcmp(header,magic,sizeof(magic))!=0 ||
       header[8]!=0xB0u || header[9]!=0u ||
       header[10]!=0u || header[11]!=0u ||
       fread(raw,1,sizeof(raw),fp)!=sizeof(raw) ||
       fgetc(fp)!=EOF)
        return false;
    uint32_t expected=(uint32_t)header[12] |
        ((uint32_t)header[13]<<8) |
        ((uint32_t)header[14]<<16) |
        ((uint32_t)header[15]<<24);
    if(crc32_bytes(raw,sizeof(raw))!=expected)
        return false;
    return ys_pc_tiles_decode(raw,sizeof(raw),out);
}
void ys_pc_tiles_grayscale(const YsPcTiles *tiles,
                           uint8_t rgb[YS_PC_ATLAS_W*YS_PC_ATLAS_H*3]) {
    if(!tiles || !rgb) return;
    for(unsigned y=0;y<YS_PC_ATLAS_H;++y)
        for(unsigned x=0;x<YS_PC_ATLAS_W;++x) {
            unsigned tile=(y/8u)*16u+x/8u;
            uint8_t value=(uint8_t)(tiles->index[tile][(y%8u)*8u+x%8u]*17u);
            size_t where=((size_t)y*YS_PC_ATLAS_W+x)*3u;
            rgb[where]=value;rgb[where+1u]=value;rgb[where+2u]=value;
        }
}
