#include "pc_sprite_sat.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t file_bytes[YS_PC_SPRITE_PACKAGE_BYTES];
static uint32_t crc32_bytes(const uint8_t *src,size_t n) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<n;++i) {
        crc^=src[i];
        for(unsigned bit=0;bit<8u;++bit)
            crc=(crc>>1)^(0xEDB88320u & (0u-(crc&1u)));
    }
    return ~crc;
}
static void checksum(void) {
    uint32_t c=crc32_bytes(file_bytes+16u,sizeof(file_bytes)-16u);
    for(unsigned k=0;k<4u;++k)
        file_bytes[12u+k]=(uint8_t)(c>>(8u*k));
}
static void make_fixture(void) {
    memset(file_bytes,0,sizeof(file_bytes));
    memcpy(file_bytes,"YSPC14S1",8);
    file_bytes[8]=YS_PC_SPRITE_RECORDS;
    unsigned len=YS_PC_SPRITE_POINTER_BYTES+YS_PC_SPRITE_STREAM_BYTES;
    file_bytes[10]=(uint8_t)len;
    file_bytes[11]=(uint8_t)(len>>8u);
    unsigned p=0x8080u;
    for(unsigned i=0;i<YS_PC_SPRITE_RECORDS;++i) {
        unsigned count=i<62u?32u:51u;
        file_bytes[16u+2u*i]=(uint8_t)p;
        file_bytes[16u+2u*i+1u]=(uint8_t)(p>>8u);
        size_t pos=16u+YS_PC_SPRITE_POINTER_BYTES+(p-0x8080u);
        file_bytes[pos]=(uint8_t)count;
        for(unsigned j=0;j<count;++j) {
            file_bytes[pos+1u+j]=(uint8_t)(j==0u?5u:1u);
            file_bytes[pos+1u+count+2u*j]=(uint8_t)(j==0u?7u:2u);
            file_bytes[pos+2u+count+2u*j]=(uint8_t)(i+j);
        }
        p+=1u+3u*count;
    }
    assert(p==0x9932u);
    checksum();
}
static bool load_asset(size_t size,YsPcSpriteRecords *out) {
    FILE *f=tmpfile();
    assert(f);
    assert(fwrite(file_bytes,1u,size,f)==size);
    rewind(f);
    bool valid=ys_pc_sprite_records_load(f,out);
    fclose(f);
    return valid;
}
static void test_fixture(void) {
    YsPcSpriteRecords records;
    make_fixture();
    assert(!ys_pc_sprite_records_load(NULL,&records));
    assert(!ys_pc_sprite_records_load(stdin,NULL));
    assert(load_asset(sizeof(file_bytes),&records));
    assert(records.pointers[0]==0x8080u);
    assert(records.pointers[63]<0x9932u);
    YsPcSatBuffer out={0};
    assert(ys_pc_sprite_stage(&records,0u,250u,252u,&out));
    assert(out.count==32u);
    assert(out.y[0]==255u && out.y[1]==0u);
    assert(out.xt[0]==3u && out.xt[1]==0u);
    assert(out.xt[2]==5u && out.xt[3]==1u);
    assert(out.y[32]==0xD0u && out.y[63]==0xD0u);
    assert(out.xt[64]==0u && out.xt[127]==0u);
    assert(ys_pc_sprite_stage(&records,63u,1u,2u,&out));
    assert(out.count==51u && out.y[51]==0xD0u);
    YsPcSatBuffer saved=out;
    assert(!ys_pc_sprite_stage(&records,64u,0u,0u,&out));
    assert(!ys_pc_sprite_stage(NULL,0u,0u,0u,&out));
    assert(!ys_pc_sprite_stage(&records,0u,0u,0u,NULL));
    assert(memcmp(&out,&saved,sizeof(out))==0);
    assert(!load_asset(sizeof(file_bytes)-1u,&records));
    file_bytes[0]='X';assert(!load_asset(sizeof(file_bytes),&records));
    make_fixture();file_bytes[8]=63u;checksum();
    assert(!load_asset(sizeof(file_bytes),&records));
    make_fixture();file_bytes[11]^=1u;checksum();
    assert(!load_asset(sizeof(file_bytes),&records));
    make_fixture();file_bytes[144u]^=1u;
    assert(!load_asset(sizeof(file_bytes),&records));
    make_fixture();file_bytes[16u]=0x7Fu;checksum();
    assert(!load_asset(sizeof(file_bytes),&records));
    make_fixture();file_bytes[16u]=file_bytes[18u];
    file_bytes[17u]=file_bytes[19u];checksum();
    assert(!load_asset(sizeof(file_bytes),&records)); /* duplicate pointer */
    make_fixture();file_bytes[144u]=65u;checksum();
    assert(!load_asset(sizeof(file_bytes),&records)); /* overlong SAT */
    make_fixture();file_bytes[144u]=0u;checksum();
    assert(!load_asset(sizeof(file_bytes),&records)); /* zero count */
    make_fixture();
    assert(load_asset(sizeof(file_bytes),&records));
    assert(ys_pc_sprite_stage(&records,0u,0u,0u,&out));
    out.y[2]=99u;
    assert(ys_pc_sprite_stage(&records,0u,0u,0u,&out));
    assert(out.y[2]==7u); /* no carryover between cases */
}
static void check_source(const char *path) {
    FILE *fp=fopen(path,"rb");assert(fp);
    YsPcSpriteRecords rec;
    assert(ys_pc_sprite_records_load(fp,&rec));
    fclose(fp);
    unsigned elems=0u, min=64u, max=0u;
    for(unsigned i=0;i<YS_PC_SPRITE_RECORDS;++i) {
        YsPcSatBuffer sat;
        assert(ys_pc_sprite_stage(&rec,i,0u,0u,&sat));
        assert(sat.count>0u && sat.count<64u);
        if(sat.count<min)min=sat.count;
        if(sat.count>max)max=sat.count;
        assert(sat.y[sat.count]==0xD0u);
        elems+=sat.count;
    }
    assert(min==27u && max==38u && elems==2086u);
    printf("PASS PC-14 original source: 64 counted SAT layouts,"
           " 2086 sprite entries, min %u max %u\n",min,max);
}
int main(int argc,char **argv) {
    assert(argc==1 || argc==2);
    test_fixture();
    if(argc==2) check_source(argv[1]);
    puts("PASS PC-14 strict 6466-byte source package, CRC,"
         " pointer full coverage, wrapped SAT deltas and termination");
    return 0;
}
