#include "pc_sat_provenance.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static YsSmsBus bus;
static YsZ80 cpu;
static YsSmsRuntime rt;
static YsPcSatProvenance a;
static void setup(void) {
    memset(&bus,0,sizeof(bus));
    memset(&cpu,0,sizeof(cpu));
    memset(&rt,0,sizeof(rt));
    memset(&a,0,sizeof(a));
    cpu.bus=&bus;rt.cpu=&cpu;cpu.pc=0x1000u;cpu.steps=1u;
    assert(ys_pc_sat_provenance_sample(&a,&rt));
    assert(ys_pc_sat_provenance_sample(&a,&rt));
    assert(a.samples==1u);
}
int main(void) {
    setup();
    assert(!ys_pc_sat_provenance_sample(NULL,&rt));
    assert(!ys_pc_sat_provenance_sample(&a,NULL));
    assert(!ys_pc_sat_provenance_upload(&a,&rt));
    assert(ys_sms_bus_write(&bus,0xDD00u,0x18u));
    assert(ys_sms_bus_write(&bus,0xDD40u,0x27u));
    cpu.pc=0x8300u;bus.mapped_bank[2]=6u;cpu.steps=2u;
    assert(ys_pc_sat_provenance_sample(&a,&rt));
    assert(a.changed==2u && a.changed_y==1u && a.changed_xt==1u);
    assert(a.site_count==1u && a.sites[0].pc==0x1000u &&
           a.sites[0].physical_bank==0u && a.sites[0].changed_bytes==2u);
    assert(ys_sms_bus_write(&bus,0xDDBFu,0x80u));
    cpu.pc=0x0427u;cpu.steps=3u;
    assert(ys_pc_sat_provenance_sample(&a,&rt));
    assert(a.sites[1].pc==0x8300u &&
           a.sites[1].physical_bank==6u && a.sites[1].changed_bytes==1u);
    assert(ys_pc_sat_provenance_upload(&a,&rt));
    assert(a.upload_count==1u && a.upload_diff_bytes==0u);
    assert(ys_pc_sat_provenance_sample(&a,&rt)); /* idempotent */
    assert(!ys_pc_sat_provenance_upload(NULL,&rt));
    cpu.pc=0x0427u;cpu.steps=4u;
    assert(ys_pc_sat_provenance_sample(&a,&rt));
    assert(ys_pc_sat_provenance_upload(&a,&rt));
    assert(a.equal_uploads==1u && a.changed_uploads==0u);
    assert(ys_sms_bus_write(&bus,0xDD00u,0x19u));
    cpu.pc=0x0427u;cpu.steps=5u;
    assert(ys_pc_sat_provenance_sample(&a,&rt));
    assert(ys_pc_sat_provenance_upload(&a,&rt));
    assert(a.changed_uploads==1u && a.upload_diff_bytes==1u &&
           a.unique_bytes==3u && a.changed==4u);
    assert(!ys_pc_sat_provenance_write(NULL,&a,&rt,"budget",5ul));
    FILE *f=tmpfile();assert(f);
    assert(!ys_pc_sat_provenance_write(f,&a,&rt,"bad",5ul));
    assert(ys_pc_sat_provenance_write(f,&a,&rt,"budget",5ul));
    rewind(f);char result[4096]={0};
    size_t n=fread(result,1u,sizeof(result)-1u,f);result[n]=0;
    assert(strstr(result,"\"changed_bytes\":4"));
    assert(strstr(result,"\"physical_bank\":6"));
    assert(strstr(result,"\"upload_diff_bytes\":1"));
    fclose(f);
    cpu.steps=4u;
    assert(!ys_pc_sat_provenance_sample(&a,&rt)); /* time regression */
    puts("PASS PC-38: passive mapped-step SAT byte deltas, wrap bounds, "
         "two source sites, upload changes and JSON rejection");
    return 0;
}
