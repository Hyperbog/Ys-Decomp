#include "pc_patterns.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint8_t asset[YS_PC_PATTERN_PACKAGE_BYTES];
static uint32_t crc32_bytes(const uint8_t *p,size_t length) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<length;++i) {
        crc^=p[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
static void seal(void) {
    uint32_t crc=crc32_bytes(asset+16u,YS_PC_PATTERN_BYTES);
    for(unsigned i=0;i<4u;++i) asset[12u+i]=(uint8_t)(crc>>(8u*i));
}
static void fixture(void) {
    memset(asset,0,sizeof(asset));
    memcpy(asset,"YSPC7P01",8u);
    asset[11u]=0x30u;
    /* Tile 1: pixel 0,0 has index 15. Pixel 7,0 has index 1. */
    for(unsigned k=0;k<4u;++k)
        asset[16u+32u+k]=(uint8_t)(0x80u|(k==0u?0x01u:0u));
    seal();
}
static bool load_bytes(size_t length,YsPcPatterns *out) {
    FILE *f=tmpfile();
    assert(f);
    assert(fwrite(asset,1,length,f)==length);
    rewind(f);
    bool ok=ys_pc_patterns_load(f,out);
    fclose(f);
    return ok;
}
static void set_word(YsPcNameTable *nt,unsigned x,unsigned y,
                     uint16_t value) {
    size_t offset=((size_t)y*YS_PC_NT_W+x)*2u;
    nt->raw[offset]=(uint8_t)value;
    nt->raw[offset+1u]=(uint8_t)(value>>8);
}
static void tests(void) {
    fixture();
    YsPcPatterns p;
    YsPcNameTable nt={0};
    YsPcPatternCoverage coverage;
    uint8_t image[YS_PC_PREVIEW_W*YS_PC_PREVIEW_H];
    uint8_t color;
    assert(!ys_pc_patterns_load(NULL,&p));
    assert(load_bytes(sizeof(asset),&p));
    assert(ys_pc_pattern_pixel(&p,1u,0u,0u,&color)&&color==15u);
    assert(ys_pc_pattern_pixel(&p,1u,7u,0u,&color)&&color==1u);
    assert(ys_pc_pattern_pixel(&p,383u,7u,7u,&color)&&color==0u);
    assert(!ys_pc_pattern_pixel(&p,384u,0u,0u,&color));
    assert(!ys_pc_pattern_pixel(&p,1u,8u,0u,&color));
    assert(!ys_pc_pattern_pixel(&p,1u,0u,8u,&color));
    assert(!ys_pc_pattern_pixel(NULL,0u,0u,0u,&color));
    assert(!ys_pc_pattern_pixel(&p,0u,0u,0u,NULL));
    set_word(&nt,0u,0u,0x0001u);
    set_word(&nt,1u,0u,0x0201u); /* horizontal flip */
    set_word(&nt,2u,0u,0x0401u); /* vertical flip */
    set_word(&nt,3u,0u,0x0180u); /* tile 384 unavailable */
    set_word(&nt,31u,23u,0x017Fu); /* tile 383 available */
    assert(ys_pc_patterns_preview(&p,&nt,image,&coverage));
    assert(coverage.matched_cells==767u && coverage.unresolved_cells==1u);
    assert(image[0]==15u && image[7]==1u);
    assert(image[8]==1u && image[15]==15u); /* H flip */
    assert(image[16]==0u && image[16+7u*256u]==15u); /* V flip */
    assert(image[24]==255u && image[24+7u*256u+7u]==255u);
    assert(image[YS_PC_PREVIEW_W*YS_PC_PREVIEW_H-1u]==0u);
    assert(!ys_pc_patterns_preview(NULL,&nt,image,&coverage));
    assert(!ys_pc_patterns_preview(&p,NULL,image,&coverage));
    assert(!ys_pc_patterns_preview(&p,&nt,NULL,&coverage));
    assert(!ys_pc_patterns_preview(&p,&nt,image,NULL));
    assert(!load_bytes(sizeof(asset)-1u,&p));
    asset[0]='?'; assert(!load_bytes(sizeof(asset),&p));
    fixture();asset[10]=1u;seal();assert(!load_bytes(sizeof(asset),&p));
    fixture();asset[16+32u]^=1u;assert(!load_bytes(sizeof(asset),&p));
}
static void source_assets(const char *patterns_path,const char *names_path) {
    FILE *file=fopen(patterns_path,"rb");
    assert(file);
    YsPcPatterns p;
    assert(ys_pc_patterns_load(file,&p));
    fclose(file);
    file=fopen(names_path,"rb");
    assert(file);
    YsPcNameTable nt;
    assert(ys_pc_nametable_load(file,&nt));
    fclose(file);
    uint8_t pixels[YS_PC_PREVIEW_W*YS_PC_PREVIEW_H];
    YsPcPatternCoverage c;
    assert(ys_pc_patterns_preview(&p,&nt,pixels,&c));
    assert(c.matched_cells+c.unresolved_cells==768u);
    for(unsigned i=0;i<YS_PC_PREVIEW_W*YS_PC_PREVIEW_H;++i)
        assert(pixels[i]==255u || pixels[i]<=15u);
    printf("PASS PC-7: 384 original source patterns; "
           "name-table pattern references covered %u, unresolved %u "
           "(preview NOT original colors or live screen)\n",
           c.matched_cells,c.unresolved_cells);
}
int main(int argc,char **argv) {
    assert(argc==1 || argc==3);
    tests();
    if(argc==3) source_assets(argv[1],argv[2]);
    puts("PASS PC-7: Mode4 planes, H/V flips, unresolved tile sentinel, CRC/bounds");
    return 0;
}
