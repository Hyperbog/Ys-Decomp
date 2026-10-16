#include "pc_collision.h"
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

enum { TOTAL=YS_PC_COLLISION_PACKAGE_BYTES };
static uint8_t bytes[TOTAL];
static uint32_t crc32_bytes(const uint8_t *data,unsigned n) {
    uint32_t crc=0xFFFFFFFFu;
    for(unsigned i=0;i<n;++i) {
        crc^=data[i];
        for(unsigned bit=0;bit<8u;++bit)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
static void seal(void) {
    uint32_t crc=crc32_bytes(bytes+16u,124u);
    for(unsigned i=0;i<4u;++i) bytes[12u+i]=(uint8_t)(crc>>(i*8u));
}
static void fixture(void) {
    memset(bytes,0,sizeof(bytes));
    memcpy(bytes,"YSPC9C01",8u);
    bytes[8u]=31u;
    bytes[10u]=4u;
    bytes[16u]=200u;bytes[17u]=20u;
    bytes[18u]=201u;bytes[19u]=20u;
    seal();
}
static bool from_bytes(size_t size,YsPcCollisionTable *out) {
    FILE *f=tmpfile();assert(f);
    assert(fwrite(bytes,1,size,f)==size);
    rewind(f);
    bool ok=ys_pc_collision_load(f,out);
    fclose(f);
    return ok;
}
static void test_synthetic(void) {
    YsPcCollisionTable data;
    fixture();
    assert(!ys_pc_collision_load(NULL,&data));
    assert(from_bytes(sizeof(bytes),&data));
    assert(data.boxes[0].y_offset==200u &&
           data.boxes[0].x_offset==201u);
    YsPcCollisionProbe probe={80u,80u,24u,0u,25u,0u};
    bool carry=false;
    assert(!ys_pc_collision_eval(NULL,0u,&probe,&carry));
    assert(!ys_pc_collision_eval(&data,31u,&probe,&carry));
    assert(!ys_pc_collision_eval(&data,0u,NULL,&carry));
    assert(!ys_pc_collision_eval(&data,0u,&probe,NULL));
    assert(ys_pc_collision_eval(&data,0u,&probe,&carry) && carry);
    probe.c=23u; /* y >= c -> reject */
    assert(ys_pc_collision_eval(&data,0u,&probe,&carry)&&!carry);
    probe.c=30u;probe.b=42u;probe.e=26u;probe.d=40u;
    assert(ys_pc_collision_eval(&data,0u,&probe,&carry)&&carry);
    probe.d=46u; /* x+20=45 < bound -> reject */
    assert(ys_pc_collision_eval(&data,0u,&probe,&carry)&&!carry);
    probe.origin_x=0u;probe.e=25u;
    assert(ys_pc_collision_eval(&data,0u,&probe,&carry)&&!carry);
    probe.origin_x=80u;probe.origin_y=0u;
    assert(ys_pc_collision_eval(&data,0u,&probe,&carry)&&!carry);
    assert(!from_bytes(TOTAL-1u,&data));
    bytes[0]='X';assert(!from_bytes(TOTAL,&data));
    fixture();bytes[8u]=30u;seal();assert(!from_bytes(TOTAL,&data));
    fixture();bytes[10u]=3u;seal();assert(!from_bytes(TOTAL,&data));
    fixture();bytes[20u]^=1u;assert(!from_bytes(TOTAL,&data));
    fixture();bytes[11u]=1u;seal();assert(!from_bytes(TOTAL,&data));
}
static void check_source(const char *filename) {
    FILE *f=fopen(filename,"rb");assert(f);
    YsPcCollisionTable bank;
    assert(ys_pc_collision_load(f,&bank));
    fclose(f);
    unsigned cases=0u,positive=0u,negative=0u;
    /* Same deterministic 31*16*8 input corpus as original Z80
       opcode interpreter in Ys/tools/bank04_collision_trace.py.
       Counts from checked-in verified original instruction trace. */
    for(unsigned i=0;i<YS_PC_COLLISION_BOXES;++i) {
        const YsPcCollisionBox *box=&bank.boxes[i];
        for(unsigned seed=0;seed<16u;++seed) {
            uint8_t oy=(uint8_t)(seed*17u+33u);
            uint8_t ox=(uint8_t)(seed*29u+51u);
            uint8_t ya=(uint8_t)((unsigned)box->y_offset+oy);
            uint8_t xa=(uint8_t)((unsigned)box->x_offset+ox);
            for(unsigned variant=0;variant<8u;++variant) {
                YsPcCollisionProbe p={
                    oy,ox,
                    (uint8_t)(ya+variant%3u),
                    (uint8_t)((unsigned)ya+box->y_extent-1u+
                              (variant/3u)%3u),
                    (uint8_t)(xa+variant%3u),
                    (uint8_t)((unsigned)xa+box->x_extent-1u+
                              (variant/3u)%3u)
                };
                bool carry=false;
                assert(ys_pc_collision_eval(&bank,i,&p,&carry));
                ++cases;
                if(carry)++positive;
                else ++negative;
            }
        }
    }
    assert(cases==3968u && positive==3033u && negative==935u);
    printf("PASS PC-9 original source bank4: %u probes, "
           "%u carry, %u no-carry; original Z80 trace corpus matches\n",
           cases,positive,negative);
}
int main(int argc,char **argv) {
    assert(argc==1||argc==2);
    test_synthetic();
    if(argc==2) check_source(argv[1]);
    puts("PASS PC-9: 31 x 4-byte collision descriptors, overflow/equality branches, CRC, bounds");
    return 0;
}
