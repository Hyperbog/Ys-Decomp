#include "pc_patterns.h"
#include <string.h>

static uint32_t crc32_bytes(const uint8_t *data,size_t size) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<size;++i) {
        crc^=data[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
bool ys_pc_patterns_load(FILE *file,YsPcPatterns *out) {
    static const uint8_t magic[8]={'Y','S','P','C','7','P','0','1'};
    uint8_t head[16];
    YsPcPatterns tmp;
    if(!file || !out ||
       fread(head,1,sizeof(head),file)!=sizeof(head) ||
       memcmp(head,magic,sizeof(magic))!=0 ||
       head[8]!=0u || head[9]!=0u ||
       head[10]!=0u || head[11]!=0x30u ||
       fread(tmp.raw,1,sizeof(tmp.raw),file)!=sizeof(tmp.raw) ||
       fgetc(file)!=EOF) return false;
    uint32_t want=(uint32_t)head[12]|
        ((uint32_t)head[13]<<8)|((uint32_t)head[14]<<16)|
        ((uint32_t)head[15]<<24);
    if(crc32_bytes(tmp.raw,sizeof(tmp.raw))!=want) return false;
    *out=tmp;
    return true;
}
bool ys_pc_pattern_pixel(const YsPcPatterns *p,unsigned tile,
                         unsigned x,unsigned y,uint8_t *result) {
    if(!p || !result || tile>=YS_PC_PATTERNS_COUNT ||
       x>=8u || y>=8u) return false;
    size_t start=(size_t)tile*32u+y*4u;
    unsigned index=0u;
    for(unsigned bit=0;bit<4u;++bit)
        index|=((unsigned)(p->raw[start+bit]>>(7u-x))&1u)<<bit;
    *result=(uint8_t)index;
    return true;
}
bool ys_pc_patterns_preview(const YsPcPatterns *patterns,
                            const YsPcNameTable *names,
                            uint8_t pixels[YS_PC_PREVIEW_W*YS_PC_PREVIEW_H],
                            YsPcPatternCoverage *coverage) {
    if(!patterns || !names || !pixels || !coverage) return false;
    YsPcPatternCoverage found={0};
    for(unsigned row=0;row<YS_PC_NT_H;++row)
        for(unsigned col=0;col<YS_PC_NT_W;++col) {
            YsPcNameCell cell;
            if(!ys_pc_nametable_cell(names,col,row,&cell)) return false;
            bool available=cell.pattern<YS_PC_PATTERNS_COUNT;
            if(available) ++found.matched_cells;
            else ++found.unresolved_cells;
            for(unsigned y=0;y<8u;++y)
                for(unsigned x=0;x<8u;++x) {
                    uint8_t color=YS_PC_PATTERN_UNRESOLVED;
                    if(available) {
                        unsigned sx=cell.horizontal_flip?7u-x:x;
                        unsigned sy=cell.vertical_flip?7u-y:y;
                        if(!ys_pc_pattern_pixel(patterns,cell.pattern,
                                                 sx,sy,&color)) return false;
                    }
                    pixels[(row*8u+y)*YS_PC_PREVIEW_W+col*8u+x]=color;
                }
        }
    *coverage=found;
    return true;
}
