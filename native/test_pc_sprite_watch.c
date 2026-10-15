#include "pc_sprite_watch.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void put(YsSmsBus *bus,uint16_t addr,uint8_t value) {
    assert(ys_sms_bus_write(bus,addr,value));
}
int main(void) {
    YsSmsBus bus={0};
    YsZ80 cpu={0};
    YsSmsVdp vdp={0};
    YsSmsRuntime rt={0};
    YsPcSpriteWatch watch={0};
    cpu.bus=&bus;cpu.vdp=&vdp;cpu.pc=0x9932u;
    cpu.ix=0xC230u;cpu.steps=1200u;
    rt.cpu=&cpu;rt.clock.vblank_events=7u;
    rt.recognized_irqs=5u;
    put(&bus,0xC199u,12u);
    put(&bus,0xC210u,77u);
    put(&bus,0xC211u,99u);
    put(&bus,0xC100u,2u);
    put(&bus,0xC028u,0x00u);put(&bus,0xC029u,0xDDu);
    put(&bus,0xC02Au,0x40u);put(&bus,0xC02Bu,0xDDu);
    assert(!ys_pc_sprite_watch_sample(NULL,&rt));
    assert(!ys_pc_sprite_watch_sample(&watch,NULL));
    assert(!ys_pc_sprite_watch_sample(&watch,&(YsSmsRuntime){0}));
    assert(ys_pc_sprite_watch_sample(&watch,&rt));
    assert(!watch.seen[3] && watch.counts[3]==0u);
    /* $9932 outside bank6 is NOT original sprite code. */
    bus.mapped_bank[2]=5u;
    assert(ys_pc_sprite_watch_sample(&watch,&rt));
    assert(!watch.seen[3]);
    bus.mapped_bank[1]=1u;
    bus.mapped_bank[2]=6u;bus.bank_select[2]=6u;
    vdp.registers[0]=4u;vdp.registers[1]=0x40u;
    vdp.registers[5]=0x7Eu;vdp.registers[6]=4u;
    vdp.vram_writes=15u;vdp.cram_writes=23u;
    assert(ys_pc_sprite_watch_sample(&watch,&rt));
    assert(watch.seen[3] && watch.counts[3]==1u);
    const YsPcSpriteWatchEvent e=watch.events[3];
    assert(e.pc==0x9932u && e.slot1==1u && e.slot2==6u);
    assert(e.selector_c199==12u && e.origin_c210==77u &&
           e.origin_c211==99u && e.c100==2u);
    assert(e.dd00==0xDD00u && e.dd40==0xDD40u &&
           e.ix==0xC230u && e.display_enabled &&
           e.vram_writes==15u && e.cram_writes==23u);
    assert(e.steps==1200u && e.irqs==5u && e.vblanks==7u);
    put(&bus,0xC199u,45u);
    cpu.steps=2100u;
    assert(ys_pc_sprite_watch_sample(&watch,&rt));
    assert(watch.counts[3]==2u);
    assert(memcmp(&watch.events[3],&e,sizeof(e))==0);
    const uint16_t pcs[4]={0x26F3u,0x26F5u,0x2704u,0x0427u};
    const unsigned mapped[4]={0u,1u,2u,4u};
    bus.mapped_bank[2]=2u;
    for(unsigned i=0;i<4u;++i) {
        cpu.pc=pcs[i];
        assert(ys_pc_sprite_watch_sample(&watch,&rt));
        assert(watch.seen[mapped[i]] &&
               watch.counts[mapped[i]]==1u);
    }
    /* Fixed-bank PCs are meaningful even without bank6 mapping. */
    assert(watch.events[2].slot2==2u);
    FILE *file=tmpfile();assert(file);
    assert(!ys_pc_sprite_watch_write(NULL,&watch,&rt,"budget",500u));
    assert(!ys_pc_sprite_watch_write(file,&watch,&rt,"invalid",500u));
    assert(ys_pc_sprite_watch_write(file,&watch,&rt,"unsupported",500u));
    rewind(file);
    char result[5200];
    size_t count=fread(result,1u,sizeof(result)-1u,file);
    result[count]=0;
    fclose(file);
    assert(strstr(result,"\"schema\": \"ys-pc15-original-sprite-watch-v1\""));
    assert(strstr(result,"\"stop_reason\": \"unsupported\""));
    assert(strstr(result,"\"pc\":\"9932\",\"seen\":true"));
    assert(strstr(result,"\"c199\":12"));
    assert(strstr(result,"\"display_enabled\":true"));
    assert(strstr(result,"\"pc\":\"0427\",\"seen\":true"));
    puts("PASS PC-15: passive source PC qualification with true"
         " physical bank6, real C199/origins, VDP on/off,"
         " first-hit invariant and bounded no-ROM JSON");
    return 0;
}
