#include "pc_source_watch.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void wr(YsSmsBus *bus,unsigned addr,unsigned value) {
    assert(ys_sms_bus_write(bus,(uint16_t)addr,(uint8_t)value));
}
int main(void) {
    YsSmsBus bus={0};
    YsZ80 cpu={0};
    YsSmsRuntime rt={0};
    YsPcSourceWatch watch={0};
    cpu.bus=&bus;cpu.pc=0x476Cu;cpu.ix=0xC230u;cpu.steps=1234u;
    rt.cpu=&cpu;rt.recognized_irqs=8u;rt.clock.vblank_events=10u;
    wr(&bus,0xC100u,0x00u);wr(&bus,0xC119u,0x04u);
    wr(&bus,0xC181u,0x95u);wr(&bus,0xC20Du,0x03u);
    wr(&bus,0xC20Eu,0x09u);wr(&bus,0xC210u,0x22u);
    wr(&bus,0xC211u,0x44u);wr(&bus,0xC23Du,0x0Cu);
    wr(&bus,0xC23Eu,0x11u);wr(&bus,0xC240u,0x88u);
    wr(&bus,0xC241u,0x99u);
    assert(!ys_pc_source_watch_sample(NULL,&rt));
    assert(!ys_pc_source_watch_sample(&watch,NULL));
    assert(!ys_pc_source_watch_sample(&watch,&(YsSmsRuntime){0}));
    assert(ys_pc_source_watch_sample(&watch,&rt));
    assert(!watch.seen[0] && watch.counts[0]==0u); /* no bank1 mapping */
    bus.mapped_bank[1]=1u;bus.mapped_bank[2]=4u;
    bus.bank_select[2]=4u;
    assert(ys_pc_source_watch_sample(&watch,&rt));
    assert(watch.seen[0] && watch.counts[0]==1u);
    assert(watch.events[0].pc==0x476Cu &&
           watch.events[0].slot1==1u && watch.events[0].slot2==4u &&
           watch.events[0].c119==4u && watch.events[0].c181==0x95u &&
           watch.events[0].c20d==3u && watch.events[0].c20e==9u &&
           watch.events[0].c210==0x22u &&
           watch.events[0].c211==0x44u &&
           watch.events[0].ix13==0x0Cu &&
           watch.events[0].ix14==0x11u &&
           watch.events[0].ix16==0x88u &&
           watch.events[0].ix17==0x99u &&
           watch.events[0].steps==1234u && watch.events[0].irqs==8u &&
           watch.events[0].vblanks==10u);
    cpu.steps=2000u;
    assert(ys_pc_source_watch_sample(&watch,&rt));
    assert(watch.counts[0]==2u && watch.events[0].steps==1234u);
    const uint16_t pcs[]={0x4773u,0x47C2u,0x486Cu,0x48DFu};
    for(unsigned i=0;i<4u;++i) {
        cpu.pc=pcs[i];
        assert(ys_pc_source_watch_sample(&watch,&rt));
        assert(watch.seen[i+1u] && watch.counts[i+1u]==1u);
    }
    assert(watch.observed_collision_calls==3u);
    FILE *out=tmpfile();assert(out);
    assert(!ys_pc_source_watch_write(NULL,&watch,&rt,"budget",200u));
    assert(!ys_pc_source_watch_write(out,&watch,&rt,"arbitrary",200u));
    assert(ys_pc_source_watch_write(out,&watch,&rt,"budget",200u));
    rewind(out);
    char text[2500];
    size_t n=fread(text,1,sizeof(text)-1u,out);
    text[n]=0;
    fclose(out);
    assert(strstr(text,"\"schema\": \"ys-pc12-source-watch-v1\"")!=NULL);
    assert(strstr(text,"\"stop_reason\": \"budget\"")!=NULL);
    assert(strstr(text,"\"observed_collision_calls\": 3")!=NULL);
    assert(strstr(text,"\"pc\":\"47C2\",\"seen\":true")!=NULL);
    assert(strstr(text,"\"c181\":149")!=NULL);
    puts("PASS PC-12: source PC + actual mapped bank1 event filter,"
         " immutable first-state WRAM/IX snapshot, bounded JSON output");
    return 0;
}
