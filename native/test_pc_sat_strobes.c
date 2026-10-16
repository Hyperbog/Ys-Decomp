#include "pc_sat_strobes.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static uint8_t image[YS_ROM_BYTES];
static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsRuntime runtime;
static YsPcSatStrobeAudit audit;

static void setup(void) {
    memset(image,0,sizeof(image));
    memset(&audit,0,sizeof(audit));
    /* Actual original Z80 instructions: LD A,$2A; LD ($DD00),A;
       LD ($FD00),A; LD ($DD40),A; LD ($DDC0),A. */
    const uint8_t program[]={0x3Eu,0x2Au,0x32u,0x00u,0xDDu,
       0x32u,0x00u,0xFDu,0x32u,0x40u,0xDDu,0x32u,0xC0u,0xDDu};
    memcpy(image+0x1000u,program,sizeof(program));
    image[6u*YS_ROM_BANK_BYTES+0x0300u]=0x32u;
    image[6u*YS_ROM_BANK_BYTES+0x0301u]=0x00u;
    image[6u*YS_ROM_BANK_BYTES+0x0302u]=0xDDu;
    assert(ys_sms_bus_init(&bus,image,sizeof(image)));
    ys_z80_reset(&cpu,&bus);
    runtime.cpu=&cpu;
    audit.cpu=&cpu;
    assert(!ys_sms_bus_set_wram_hook(NULL,ys_pc_sat_strobes_hook,&audit));
    assert(!ys_sms_bus_set_wram_hook(&bus,ys_pc_sat_strobes_hook,NULL));
    assert(!ys_sms_bus_set_wram_hook(&bus,NULL,&audit));
    assert(ys_sms_bus_set_wram_hook(&bus,ys_pc_sat_strobes_hook,&audit));
    cpu.pc=0x1000u;
}
static void test_wram_and_bank_strobes(void) {
    setup();
    for(unsigned i=0u;i<5u;++i)
        assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(audit.count[0]==3u);
    assert(audit.same[0]==1u && audit.changed[0]==2u);
    assert(audit.alias[0]==1u && audit.unique[0]==2u);
    assert(audit.y[0]==2u && audit.xt[0]==1u);
    /* Real bank6 opcode must be attributed to its original START PC,
       not the PC following its immediate address bytes. */
    bus.mapped_bank[2]=6u;
    cpu.pc=0x8300u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(audit.count[0]==4u && audit.same[0]==2u);
    bool mapped=false;
    for(unsigned i=0;i<audit.site_count;++i)
        if(audit.sites[i].pc==0x8300u &&
           audit.sites[i].bank==6u && audit.sites[i].count==1u)
            mapped=true;
    assert(mapped);
    assert(!ys_pc_sat_strobes_set_phase(NULL,1u));
    assert(!ys_pc_sat_strobes_set_phase(&audit,2u));
    assert(ys_pc_sat_strobes_set_phase(&audit,1u));
    assert(!ys_pc_sat_strobes_set_phase(&audit,0u));
    cpu.a=0x2Bu;cpu.pc=0x1002u;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(audit.count[1]==1u && audit.changed[1]==1u);
    /* Successful writes to SRAM-mapped C000-FFFF are NOT WRAM strobes. */
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x10u));
    assert(ys_sms_bus_write(&bus,0xDD00u,0x99u));
    assert(audit.count[1]==1u);
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x00u));
    assert(!ys_sms_bus_write(&bus,0x4000u,0x99u));
    assert(audit.count[1]==1u);
    /* Genuine Z80 IM1 stack push: two writes to DD01,DD00, never
       misattributed to the interrupted $1002 source instruction. */
    cpu.pc=0x0065u;cpu.sp=0xDD02u;
    cpu.iff1=true;cpu.interrupt_mode=1u;
    assert(ys_z80_irq(&cpu));
    assert(audit.count[1]==3u && audit.irq[1]==2u);
    assert(audit.y[1]==3u && audit.xt[1]==0u);
    bool irq_site=false;
    for(unsigned i=0;i<audit.site_count;++i)
        if(audit.sites[i].irq && audit.sites[i].pc==0x0038u &&
           audit.sites[i].bank==0u && audit.sites[i].count==2u)
            irq_site=true;
    assert(irq_site && !cpu.irq_write_active);
    FILE *f=tmpfile();assert(f);
    assert(!ys_pc_sat_strobes_write(f,&audit,&runtime,"invented",300000ul));
    assert(ys_pc_sat_strobes_write(f,&audit,&runtime,"budget",300000ul));
    rewind(f);char json[8192]={0};
    size_t len=fread(json,1,sizeof(json)-1u,f);
    json[len]=0;fclose(f);
    assert(strstr(json,"ys-pc39-original-sat-wram-strobes-v1"));
    assert(strstr(json,"\"alias\":1"));
    assert(strstr(json,"\"irq\":true"));
    audit.overflow=true;
    f=tmpfile();assert(f);
    assert(!ys_pc_sat_strobes_write(f,&audit,&runtime,"budget",300000ul));
    fclose(f);
    audit.overflow=false;
    assert(ys_sms_bus_set_wram_hook(&bus,NULL,NULL));
    assert(ys_sms_bus_write(&bus,0xDD00u,0x70u));
    assert(audit.count[1]==3u);
}
int main(void) {
    test_wram_and_bank_strobes();
    puts("PASS PC-39: actual same/changed WRAM stores, FD alias,"
         " mapped opcode PC, ROM rejection, cart RAM and IM1 attribution");
    return 0;
}
