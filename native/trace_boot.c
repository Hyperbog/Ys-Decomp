#include "z80.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fail(const char *what, const YsZ80 *cpu) {
    fprintf(stderr,"FAIL %s: steps=%llu PC=$%04X fault=$%04X status=%s\n",
            what,(unsigned long long)cpu->steps,cpu->pc,cpu->fault_pc,
            ys_z80_status_name(cpu->status));
    return EXIT_FAILURE;
}
int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr,"usage: ys-native-trace /path/to/source-built.sms\n");
        return EXIT_FAILURE;
    }
    FILE *in=fopen(argv[1],"rb");
    if (!in) {perror("open");return EXIT_FAILURE;}
    uint8_t *rom=malloc(YS_ROM_BYTES);
    YsSmsBus *bus=malloc(sizeof(*bus));
    YsSmsVdp *vdp=malloc(sizeof(*vdp));
    YsSmsSound *sound=malloc(sizeof(*sound));
    if (!rom || !bus || !vdp || !sound) {
        fclose(in);free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
    }
    size_t size=fread(rom,1,YS_ROM_BYTES,in);
    int trailing=fgetc(in);
    fclose(in);
    if (size!=YS_ROM_BYTES || trailing!=EOF ||
        memcmp(rom+0x7FF0,"TMR SEGA",8)!=0 ||
        !ys_sms_bus_init(bus,rom,size)) {
        fputs("invalid Ys-sized image; SHA-256 check belongs to M10 builder\n",stderr);
        free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
    }
    YsZ80 cpu;
    ys_z80_reset(&cpu,bus);
    ys_sms_vdp_reset(vdp);
    ys_sms_sound_reset(sound);
    ys_z80_attach_vdp(&cpu,vdp);
    ys_z80_attach_sound(&cpu,sound);
    /* Continuous reset, battery-backed SRAM setup, two RAM clear loops,
       bank 2 sound initializer $8803, and VDP initializer $0749. */
    Z80Status result=ys_z80_run_until(&cpu,0x00C1,30000);
    bool ok=result==Z80_RUNNING && cpu.pc==0x00C1 &&
        cpu.sp==0xDFF0 && cpu.interrupt_mode==1 &&
        bus->mapper_control==0x80 && bus->mapped_bank[0]==0 &&
        bus->mapped_bank[1]==1 && bus->mapped_bank[2]==2 &&
        ys_sms_bus_read(bus,0xC001)==0xFF &&
        ys_sms_bus_read(bus,0xDE60)==0 &&
        ys_sms_bus_read(bus,0xDE63)==0 &&
        ys_sms_bus_read(bus,0xDE68)==0xE4 &&
        memcmp(bus->cart_ram+0x0010,rom+0x0782,0x18)==0 &&
        sound->psg_write_count==11 &&
        memcmp(sound->psg_prefix,rom+0x8878,11)==0 &&
        sound->fm_address_count==6 && sound->fm_data_count==6 &&
        vdp->register_writes==11 && vdp->control_writes==24 &&
        vdp->cram_writes==1 && vdp->vram_writes==0 &&
        vdp->cram[0x10]==0 && vdp->address==0x11 &&
        memcmp(vdp->registers,rom+0x0768,11)==0 &&
        memcmp(bus->wram+0x0010,rom+0x0768,11)==0;
    for (unsigned i=0;i<6;++i)
        ok=ok && sound->fm_touched[0x20u+i] &&
            sound->fm_registers[0x20u+i]==0;
    if (!ok) {
        int code=fail("continuous bank-2 sound + bank-0 VDP initialization",&cpu);
        fprintf(stderr,"  PSG=%llu FM=%llu/%llu VDP register=%llu ctrl=%llu CRAM=%llu\n",
                (unsigned long long)sound->psg_write_count,
                (unsigned long long)sound->fm_address_count,
                (unsigned long long)sound->fm_data_count,
                (unsigned long long)vdp->register_writes,
                (unsigned long long)vdp->control_writes,
                (unsigned long long)vdp->cram_writes);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS continuous Ys reset through bank-2 sound and VDP: %llu instructions, PC=$%04X\n",
           (unsigned long long)cpu.steps,cpu.pc);
    puts("PASS source-matched PSG=11 bytes, FM=6 register/data pairs, VDP=11 registers + 1 CRAM byte");
    /* Phase 5: execute the actual $0BC5 context-saving bridge and the
       $0042 VBlank wait until its EI has executed. There is no synthetic
       frame clock: the event below is injected deliberately and separately. */
    /* Continuous CALL $0BC5 also pushes $00C4 before the bridge itself. */
    result=ys_z80_run_until(&cpu,0x0046,128);
    if (result!=Z80_RUNNING || cpu.pc!=0x0046 ||
        cpu.sp!=0xDFD6 || cpu.ei_delay!=1 ||
        !cpu.iff1 || ys_sms_bus_read(bus,0xC021)!=1 ||
        bus->mapped_bank[2]!=2) {
        int code=fail("saved register context and VBlank wait entry",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    if (ys_z80_irq(&cpu)) {
        fputs("FAIL: maskable IRQ accepted during EI defer\n",stderr);
        free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
    }
    result=ys_z80_run_until(&cpu,0x0049,1);
    if (result!=Z80_RUNNING || cpu.a!=1 || cpu.ei_delay!=0) {
        int code=fail("VBlank wait load after EI defer",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    vdp->status |= 0x80; /* Explicit test event, NOT emulated scanline timing. */
    if (!ys_z80_irq(&cpu) || cpu.pc!=0x0038 || cpu.sp!=0xDFD4 ||
        ys_sms_bus_read(bus,0xDFD4)!=0x49 ||
        ys_sms_bus_read(bus,0xDFD5)!=0 ||
        cpu.iff1) {
        int code=fail("explicit maskable IM1 interrupt",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    result=ys_z80_run_until(&cpu,0x0102,5);
    if (result!=Z80_RUNNING || cpu.pc!=0x0102 ||
        cpu.a!=0x80 || vdp->status!=0 || cpu.sp!=0xDFD2) {
        int code=fail("actual Ys IM1 ISR and VDP status read",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    result=ys_z80_run_until(&cpu,0x0108,3);
    if (result!=Z80_RUNNING || cpu.a!=1 ||
        ys_sms_bus_read(bus,0xC021)!=1 || cpu.sp!=0xDFD2) {
        int code=fail("actual Ys VBlank-state dispatch",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS Ys VBlank wait + explicit IM1 entry: %llu instructions, PC=$%04X SP=$%04X\n",
           (unsigned long long)cpu.steps,cpu.pc,cpu.sp);
    puts("Stop before $0108 ISR body: VBlank event was injected, not clock-generated.");
    puts("No full boot, input, frame rendering, sound synthesis or gameplay claim.");
    free(rom);free(bus);free(vdp);free(sound);
    return EXIT_SUCCESS;
}
