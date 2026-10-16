#include "pc44_c198_writes.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t rom[YS_ROM_BYTES];
static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsRuntime rt;
static YsPc44Writer writer;
static void step_at(uint16_t pc,uint8_t value) {
    cpu.status=Z80_RUNNING;cpu.pc=pc;cpu.a=value;
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
}
int main(void) {
    memset(rom,0,sizeof(rom));
    assert(ys_sms_bus_init(&bus,rom,sizeof(rom)));
    ys_z80_reset(&cpu,&bus);
    memset(&rt,0,sizeof(rt));rt.cpu=&cpu;
    memset(&writer,0,sizeof(writer));writer.cpu=&cpu;
    /* Original independently source-listed writes: $2041/$2281. */
    rom[0x2041u]=0x32u;rom[0x2042u]=0x98u;rom[0x2043u]=0xC1u;
    rom[0x2281u]=0x32u;rom[0x2282u]=0x98u;rom[0x2283u]=0xC1u;
    rom[0x0120u]=0x32u;rom[0x0121u]=0x98u;rom[0x0122u]=0xE1u;
    rom[0x0124u]=0x32u;rom[0x0125u]=0x00u;rom[0x0126u]=0x40u;
    assert(ys_sms_bus_set_wram_hook(&bus,ys_pc44_c198_hook,&writer));
    step_at(0x2041u,0u);
    assert(writer.count==1u && writer.same[0]==1u &&
           writer.changed[0]==0u);
    assert(writer.writes[0].pc==0x2041u &&
           writer.writes[0].bank==0u &&
           writer.writes[0].before==0u &&
           writer.writes[0].after==0u);
    step_at(0x2281u,3u);
    assert(writer.count==2u && writer.changed[0]==1u);
    assert(writer.writes[1].before==0u &&
           writer.writes[1].after==3u &&
           writer.writes[1].a==3u);
    assert(ys_pc44_set_phase(&writer,1u));
    writer.iteration=526990ul;
    step_at(0x2041u,3u);
    assert(writer.count==3u && writer.same[1]==1u &&
           writer.writes[2].iteration==526990ul &&
           writer.writes[2].phase==1u);
    /* Mirrored $E198 is the SAME physical console WRAM byte. */
    writer.iteration=526991ul;
    step_at(0x0120u,5u);
    assert(writer.count==4u && writer.aliases[1]==1u &&
           writer.changed[1]==1u &&
           writer.writes[3].logical==0xE198u &&
           writer.writes[3].pc==0x0120u &&
           writer.writes[3].bank==0u &&
           writer.writes[3].after==5u);
    /* Physical ROM refusal cannot produce a false C198 strobe. */
    writer.iteration=526992ul;
    cpu.status=Z80_RUNNING;cpu.pc=0x0124u;cpu.a=6u;
    assert(ys_z80_step(&cpu)==Z80_BAD_WRITE);
    assert(writer.count==4u);
    /* SRAM mapping excludes C198 physical console WRAM writes. */
    assert(ys_sms_bus_write(&bus,0xFFFCu,0x10u));
    writer.iteration=526993ul;
    step_at(0x2041u,7u);
    assert(writer.count==4u);
    assert(bus.cart_ram[0x0198u]==7u &&
           bus.wram[0x0198u]==5u);
    assert(ys_sms_bus_write(&bus,0xFFFCu,0u));
    writer.iteration=526994ul;
    step_at(0x2041u,7u);
    assert(writer.count==5u &&
           writer.changed[1]==2u &&
           writer.writes[4].before==5u &&
           writer.writes[4].after==7u);
    assert(!ys_pc44_set_phase(&writer,0u));
    assert(writer.phase_counts[0]==2u &&
           writer.phase_counts[1]==3u);
    FILE *file=tmpfile();assert(file);
    assert(!ys_pc44_write_report(file,&writer,&rt,"unsupported",600000ul));
    assert(ys_pc44_write_report(file,&writer,&rt,"budget",600000ul));
    rewind(file);
    char buffer[5000]={0};
    size_t count=fread(buffer,1,sizeof(buffer)-1u,file);
    buffer[count]=0;fclose(file);
    assert(strstr(buffer,"ys-pc44-physical-c198-writes-v1"));
    assert(strstr(buffer,"\"phase_counts\":[2,3]"));
    assert(strstr(buffer,"\"same\":[1,1]"));
    assert(strstr(buffer,"\"changed\":[1,2]"));
    assert(strstr(buffer,"\"aliases\":[0,1]"));
    assert(strstr(buffer,"\"pc\":\"2041\""));
    assert(strstr(buffer,"\"pc\":\"2281\""));
    assert(ys_sms_bus_set_wram_hook(&bus,NULL,NULL));
    puts("PASS PC-44: source opcodes $2041/$2281, identical WRAM"
         " stores, aliases, SRAM exclusion, ROM refusal and phases");
    return 0;
}
