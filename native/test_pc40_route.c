#include "pc40_route.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsRuntime rt;
static YsPc40Route watch;
static void reset_fixture(void) {
    memset(&bus,0,sizeof(bus));
    memset(&cpu,0,sizeof(cpu));
    memset(&rt,0,sizeof(rt));
    memset(&watch,0,sizeof(watch));
    cpu.bus=&bus;rt.cpu=&cpu;
    cpu.pc=0x26F3u;
    bus.mapped_bank[0]=0u;
    bus.mapped_bank[1]=1u;
    bus.mapped_bank[2]=6u;
    cpu.steps=50u;
}
int main(void) {
    reset_fixture();
    assert(!ys_pc40_route_sample(NULL,&rt,0));
    assert(!ys_pc40_route_sample(&watch,NULL,0));
    assert(!ys_pc40_route_mark_prefix(&watch,&rt,299999ul,
                                      (uint32_t[5]){0},0));
    assert(ys_pc40_route_sample(&watch,&rt,0ul));
    assert(watch.events[0][2].hits==1u &&
           watch.events[0][2].first_step==50u);
    cpu.pc=0x9932u;cpu.steps++;
    assert(ys_pc40_route_sample(&watch,&rt,1ul));
    assert(watch.events[0][6].hits==1u);
    bus.mapped_bank[2]=8u;cpu.steps++;
    assert(ys_pc40_route_sample(&watch,&rt,2ul));
    assert(watch.events[0][6].hits==1u); /* false mapper hit */
    cpu.pc=0x4773u;cpu.steps++;
    assert(ys_pc40_route_sample(&watch,&rt,3ul));
    assert(watch.events[0][8].hits==1u);
    bus.mapped_bank[1]=3u;cpu.steps++;
    assert(ys_pc40_route_sample(&watch,&rt,4ul));
    assert(watch.events[0][8].hits==1u);
    for(unsigned long i=5ul;i<300000ul;++i) {
        cpu.pc=0x0030u;
        assert(ys_pc40_route_sample(&watch,&rt,i));
    }
    assert(!ys_pc40_route_sample(&watch,&rt,300000ul));
    assert(!ys_pc40_route_mark_prefix(&watch,&rt,300000ul,NULL,0u));
    uint32_t sprite[5]={1u,2u,3u,4u,5u};
    rt.recognized_irqs=100u;rt.clock.vblank_events=104u;
    assert(ys_pc40_route_mark_prefix(&watch,&rt,300000ul,sprite,0u));
    assert(!ys_pc40_route_mark_prefix(&watch,&rt,300000ul,sprite,0u));
    assert(watch.prefix_pc==0x0030u && watch.prefix_sprite[3]==4u);
    cpu.pc=0x9932u;cpu.steps++;
    bus.mapped_bank[2]=6u;
    assert(ys_pc40_route_sample(&watch,&rt,300000ul));
    assert(watch.events[1][6].hits==1u &&
           watch.events[0][6].hits==1u);
    FILE *f=tmpfile();assert(f);
    assert(!ys_pc40_route_write(f,&watch,&rt,"untrusted",300001ul));
    assert(ys_pc40_route_write(f,&watch,&rt,"unsupported",300001ul));
    /* Natural break immediately after sampling iteration 300000:
       observed 300001 boundaries, loop counter still 300000. */
    FILE *early=tmpfile();assert(early);
    assert(ys_pc40_route_write(early,&watch,&rt,
                               "collision_observed",300000ul));
    assert(!ys_pc40_route_write(early,&watch,&rt,"budget",300000ul));
    fclose(early);
    rewind(f);
    char output[7000]={0};
    size_t n=fread(output,1,sizeof(output)-1u,f);
    output[n]=0;fclose(f);
    assert(strstr(output,"ys-pc40-source-route-600k-v1"));
    assert(strstr(output,"\"prefix_steps\":300000"));
    assert(strstr(output,"\"prefix_sprite\":[1,2,3,4,5]"));
    assert(strstr(output,"\"phase\":1,\"pc\":\"9932\""));
    assert(!ys_pc40_route_sample(&watch,&rt,300000ul)); /* duplicate */
    puts("PASS PC-40: bank-qualified original route, prefix boundary,"
         " negative mapper hits, source route serialization");
    return 0;
}
