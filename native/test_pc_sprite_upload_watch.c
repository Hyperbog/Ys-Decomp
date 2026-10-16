#include "pc_sprite_upload_watch.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsVdp vdp;
static YsSmsRuntime runtime;
static YsPcSpriteUploadWatch watch;
static void setup(void) {
    memset(&bus,0,sizeof(bus));
    memset(&cpu,0,sizeof(cpu));
    memset(&vdp,0,sizeof(vdp));
    memset(&runtime,0,sizeof(runtime));
    memset(&watch,0,sizeof(watch));
    cpu.bus=&bus;cpu.vdp=&vdp;runtime.cpu=&cpu;
    cpu.steps=10u;cpu.pc=0x0427u;
    for(unsigned i=0;i<64u;++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xDD00u+i),(uint8_t)(i+3u)));
    for(unsigned i=0;i<128u;++i)
        assert(ys_sms_bus_write(&bus,(uint16_t)(0xDD40u+i),(uint8_t)(i*3u)));
}
static void upload_y(void) {
    for(unsigned i=0;i<64u;++i)
        vdp.vram[0x3F00u+i]=ys_sms_bus_read(&bus,(uint16_t)(0xDD00u+i));
    vdp.vram_writes+=64u;
}
static void upload_xt(void) {
    for(unsigned i=0;i<128u;++i)
        vdp.vram[0x3F80u+i]=ys_sms_bus_read(&bus,(uint16_t)(0xDD40u+i));
    vdp.vram_writes+=128u;
}
static void test_two_returns_and_integrity(void) {
    setup();
    assert(!ys_pc_sprite_upload_watch_sample(NULL,&runtime));
    assert(!ys_pc_sprite_upload_watch_sample(&watch,NULL));
    assert(!ys_pc_sprite_upload_watch_sample(&watch,&(YsSmsRuntime){0}));
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(watch.entries==1u && watch.active);
    upload_y();
    cpu.pc=0x053Fu;cpu.steps=75u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(watch.halfway==1u && watch.completed==0u && watch.active);
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(watch.halfway==1u);
    upload_xt();
    cpu.pc=0x0436u;cpu.steps=76u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    cpu.pc=0x053Fu;cpu.steps=210u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(watch.entries==1u && watch.halfway==1u &&
           watch.completed==1u && watch.matched==1u &&
           watch.mismatched==0u && !watch.active &&
           watch.bytes_compared==192u && watch.bytes_different==0u &&
           watch.first_source_crc==watch.first_vram_crc &&
           watch.last_source_crc==watch.last_vram_crc &&
           watch.last_write_delta==192u);
    cpu.pc=0x0427u;cpu.steps=211u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    upload_y();
    cpu.pc=0x053Fu;cpu.steps=275u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    upload_xt();
    vdp.vram[0x3F80u]^=1u;
    cpu.pc=0x053Fu;cpu.steps=400u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(watch.completed==2u && watch.halfway==2u &&
           watch.matched==1u && watch.mismatched==1u &&
           watch.bytes_compared==384u && watch.bytes_different==1u &&
           watch.first_mismatch_1based==65u &&
           watch.last_source_crc!=watch.last_vram_crc);
    FILE *file=tmpfile();assert(file);
    assert(!ys_pc_sprite_upload_watch_write(file,&watch,&runtime,
                                             "invented",400ul));
    assert(ys_pc_sprite_upload_watch_write(file,&watch,&runtime,
                                            "budget",400ul));
    rewind(file);
    char buffer[3000];
    size_t count=fread(buffer,1u,sizeof(buffer)-1u,file);
    buffer[count]=0;fclose(file);
    assert(strstr(buffer,"\"schema\":\"ys-pc36-sat-source-upload-v1\""));
    assert(strstr(buffer,"\"entries\":2,\"halfway\":2"));
    assert(strstr(buffer,"\"bytes_different\":1"));
}
static void test_abandonment(void) {
    setup();
    cpu.pc=0x053Fu;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(watch.entries==0u);
    cpu.pc=0x0427u;cpu.steps=11u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    cpu.steps=12u;
    assert(ys_pc_sprite_upload_watch_sample(&watch,&runtime));
    assert(watch.entries==2u && watch.abandoned==1u &&
           watch.active && watch.completed==0u);
    FILE *file=tmpfile();assert(file);
    assert(ys_pc_sprite_upload_watch_write(file,&watch,&runtime,
                                           "unsupported",2ul));
    fclose(file);
}
int main(void) {
    test_two_returns_and_integrity();
    test_abandonment();
    puts("PASS PC-36: original double-return 64+128-byte SAT upload"
         " source snapshot/VRAM comparison, CRC and failure cases");
    return 0;
}
