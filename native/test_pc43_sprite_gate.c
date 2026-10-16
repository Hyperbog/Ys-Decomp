#include "pc43_sprite_gate.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t rom[YS_ROM_BYTES];
static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsRuntime rt;
static YsPc43SpriteGate watch;
static void init_fixture(void) {
    memset(rom,0,sizeof(rom));
    memset(&rt,0,sizeof(rt));
    memset(&watch,0,sizeof(watch));
    assert(ys_sms_bus_init(&bus,rom,sizeof(rom)));
    ys_z80_reset(&cpu,&bus);
    rt.cpu=&cpu;
    bus.mapped_bank[2]=6u;
    /* CALL $9932 must push on ordinary WRAM, not FFFE/FFFF
       mapper registers when the reset SP would otherwise be 0. */
    cpu.sp=0xDFF0u;
    /* Genuine original physical bank6 source opcodes; missing
       unrelated producer bytes never executed in this fixture. */
    const uint8_t op[]={0x3Au,0x98u,0xC1u,0xB7u,0x28u,0x5Au,
                         0xCDu,0x32u,0x99u};
    memcpy(rom+6u*YS_ROM_BANK_BYTES+0x1966u,op,sizeof(op));
}
static void execute_one(unsigned long step) {
    assert(ys_pc43_gate_pre(&watch,&rt,step));
    assert(ys_z80_step(&cpu)==Z80_RUNNING);
    assert(ys_pc43_gate_post(&watch,&rt,step));
}
static void execute_gate(unsigned long first,unsigned value) {
    assert(ys_sms_bus_write(&bus,0xC198u,(uint8_t)value));
    cpu.pc=0x9966u;
    execute_one(first);         /* LD A,($C198) */
    assert(cpu.pc==0x9969u && cpu.a==value);
    execute_one(first+1ul);     /* OR A */
    assert(cpu.pc==0x996Au);
    execute_one(first+2ul);     /* JR Z,$99C6 */
    assert(cpu.pc==(value==0u?0x99C6u:0x996Cu));
    assert(watch.entries[watch.count-1u].successor_seen);
}
int main(void) {
    init_fixture();
    execute_gate(0ul,0u);
    assert(watch.count==1u && watch.gate_hits==1u);
    assert(watch.branch_zero==1u && watch.branch_nonzero==0u);
    assert(watch.entries[0].c198_entry==0u);
    assert(watch.entries[0].a_gate==0u &&
           watch.entries[0].c198_gate==0u);
    assert(watch.entries[0].or_seen && watch.entries[0].gate_seen);
    assert(watch.entries[0].successor_pc==0x99C6u);
    assert(watch.branch_mismatch==0u && watch.orphan_gates==0u);
    /* Next sample at actual source branch target; no CALL. */
    execute_one(3ul);
    assert(watch.skip_targets==1u && watch.producer_entries==0u &&
           watch.call_sites==0u);
    execute_gate(4ul,1u);
    assert(watch.count==2u && watch.branch_nonzero==1u);
    assert(watch.entries[1].c198_entry==1u &&
           watch.entries[1].a_gate==1u);
    assert(watch.entries[1].successor_pc==0x996Cu);
    execute_one(7ul);          /* real CALL $9932 */
    assert(cpu.pc==0x9932u && watch.call_sites==1u);
    execute_one(8ul);          /* observe producer-site opcode */
    assert(watch.producer_entries==1u);
    assert(watch.gate_hits==2u && watch.or_hits==2u);
    /* Identical virtual address in wrong physical bank cannot count. */
    cpu.pc=0x9966u;bus.mapped_bank[2]=7u;
    execute_one(9ul);
    assert(watch.count==2u);
    cpu.pc=0x9966u;bus.mapped_bank[2]=6u;
    bus.mapper_control=0x08u; /* slot 2 SRAM, not original ROM */
    assert(ys_pc43_gate_pre(&watch,&rt,10ul));
    assert(ys_pc43_gate_post(&watch,&rt,10ul));
    assert(watch.count==2u);
    bus.mapper_control=0u;
    /* Reject missing mandatory post-step, duplicate iterations,
       and apparent non-budget reports. */
    cpu.pc=0x996Au;
    assert(ys_pc43_gate_pre(&watch,&rt,11ul));
    assert(!ys_pc43_gate_pre(&watch,&rt,12ul));
    assert(ys_pc43_gate_post(&watch,&rt,11ul));
    assert(watch.orphan_gates==1u);
    assert(!ys_pc43_gate_post(&watch,&rt,12ul));
    FILE *bad=tmpfile();assert(bad);
    assert(!ys_pc43_gate_write(bad,&watch,&rt,"unsupported",600000ul));
    fclose(bad);
    /* Serialization format is small and stable, distinct from
       golden source-ROM observations. */
    watch.observed_iterations=600000ul;
    FILE *out=tmpfile();assert(out);
    assert(ys_pc43_gate_write(out,&watch,&rt,"budget",600000ul));
    rewind(out);
    char buf[5000]={0};
    size_t n=fread(buf,1,sizeof(buf)-1u,out);
    buf[n]=0;fclose(out);
    assert(strstr(buf,"ys-pc43-original-bank6-c198-gate-v1"));
    assert(strstr(buf,"\"branch_zero\":1"));
    assert(strstr(buf,"\"branch_nonzero\":1"));
    assert(strstr(buf,"\"c198_entry\":0"));
    assert(strstr(buf,"\"c198_entry\":1"));
    puts("PASS PC-43: original bank6 gate both branches, physical"
         " mapper filter, source JR successors and strict reports");
    return 0;
}
