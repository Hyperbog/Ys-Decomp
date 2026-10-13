#include "z80.h"
#include "sms_video.h"
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
    if (!(argc==2 || (argc==4 && strcmp(argv[2],"--frame")==0))) {
        fprintf(stderr,"usage: ys-native-trace /path/to/source-built.sms [--frame output.ppm]\n");
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
    YsSmsInput input;
    ys_sms_input_reset(&input);
    ys_z80_attach_input(&cpu,&input);
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
    const YsZ80 initial_context=cpu; /* Registers before CALL $0BC5. */
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
    /* M22: the real ISR emits four additional VDP register commands via
       OUTD/OUT (C),r and dispatches the one-based C021 state via RST $08.
       No other VBlank event or CPU/device state is injected. */
    const uint8_t reg10=ys_sms_bus_read(bus,0xC01A);
    const uint8_t reg9=ys_sms_bus_read(bus,0xC019);
    const uint8_t reg8=ys_sms_bus_read(bus,0xC018);
    result=ys_z80_run_until(&cpu,0x01B4,48);
    if (result!=Z80_RUNNING || cpu.pc!=0x01B4 ||
        cpu.sp!=0xDFD0 || cpu.a!=0xB4 ||
        cpu.h!=0x01 || cpu.l!=0xB4 ||
        cpu.b!=0x88 || cpu.c!=0xBF ||
        ys_sms_bus_read(bus,0xDFD0)!=0x25 ||
        ys_sms_bus_read(bus,0xDFD1)!=0x01 ||
        vdp->register_writes!=15 ||
        vdp->control_writes!=32 ||
        vdp->registers[10]!=reg10 ||
        vdp->registers[9]!=reg9 ||
        vdp->registers[8]!=reg8 ||
        vdp->registers[5]!=0xFF ||
        vdp->cram_writes!=1 ||
        vdp->vram_writes!=0) {
        int code=fail("Ys first VBlank VDP commands and RST $08 dispatch",&cpu);
        fprintf(stderr,"  VDP regs=%llu ctrl=%llu r10=%02X/%02X r9=%02X/%02X r8=%02X/%02X r5=%02X\n",
                (unsigned long long)vdp->register_writes,
                (unsigned long long)vdp->control_writes,
                vdp->registers[10],reg10,vdp->registers[9],reg9,
                vdp->registers[8],reg8,vdp->registers[5]);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS Ys first VBlank VDP update and RST $08 dispatch: %llu instructions, PC=$%04X SP=$%04X\n",
           (unsigned long long)cpu.steps,cpu.pc,cpu.sp);
    /* M23: continue through $01B4->$0427 unrolled sprite-table output
       ($04BF:64 bytes, $043F:128 bytes), then $03E8 RET Z and the
       $0773 idle-controller sample. Stop at bank-2 $8000 before sound update. */
    result=ys_z80_run_until(&cpu,0x0125,256);
    bool sprites_ok=result==Z80_RUNNING && cpu.pc==0x0125 &&
        cpu.sp==0xDFD2 && vdp->control_writes==36 &&
        vdp->register_writes==15 && vdp->vram_writes==192 &&
        vdp->address==0 && vdp->code==1 &&
        ys_sms_bus_read(bus,0xC02C)==0;
    for (unsigned i=0;i<64;++i)
        sprites_ok=sprites_ok &&
            vdp->vram[0x3F00u+i]==ys_sms_bus_read(bus,(uint16_t)(0xDD00u+i));
    for (unsigned i=0;i<128;++i)
        sprites_ok=sprites_ok &&
            vdp->vram[0x3F80u+i]==ys_sms_bus_read(bus,(uint16_t)(0xDD40u+i));
    if (!sprites_ok) {
        int code=fail("real first-frame sprite-table transfer and RST return",&cpu);
        fprintf(stderr,"  VDP VRAM writes=%llu control writes=%llu addr=$%04X\n",
                (unsigned long long)vdp->vram_writes,
                (unsigned long long)vdp->control_writes,vdp->address);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS source sprite-table uploads: 64 Y + 128 X/tile bytes, PC=$%04X\n",cpu.pc);

    result=ys_z80_run_until(&cpu,0x0130,20);
    if (result!=Z80_RUNNING || cpu.pc!=0x0130 ||
        input.reads_dc!=1 || input.reads_dd!=0 ||
        ys_sms_bus_read(bus,0xC01B)!=0 ||
        ys_sms_bus_read(bus,0xC01C)!=0 ||
        !cpu.iff1 || cpu.ei_delay!=0 || cpu.sp!=0xDFD2) {
        int code=fail("real idle-controller sample and interrupt re-enable",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    result=ys_z80_run_until(&cpu,0x8000,3);
    if (result!=Z80_RUNNING || cpu.pc!=0x8000 ||
        cpu.sp!=0xDFD0 || bus->mapped_bank[2]!=2 ||
        ys_sms_bus_read(bus,0xDFD0)!=0x38 ||
        ys_sms_bus_read(bus,0xDFD1)!=0x01) {
        int code=fail("first VBlank dispatch into bank-2 sound frame update",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS first VBlank sprite and input processing: %llu instructions, PC=$%04X SP=$%04X\n",
           (unsigned long long)cpu.steps,cpu.pc,cpu.sp);
    /* M24: continue actual bank-2 first-frame sound update, including the
       zero-state branch through $8803 and the six inactive IX channels.
       No PSG/FM response or video tick is fabricated. */
    result=ys_z80_run_until(&cpu,0x0138,2000);
    if (result!=Z80_RUNNING || cpu.pc!=0x0138 ||
        cpu.sp!=0xDFD2 || bus->mapped_bank[2]!=2 ||
        sound->psg_write_count!=22 ||
        sound->fm_address_count!=12 || sound->fm_data_count!=12 ||
        ys_sms_bus_read(bus,0xDE63)!=0 ||
        ys_sms_bus_read(bus,0xDE68)!=0xE4) {
        int code=fail("first-frame bank-2 $8000 sound update",&cpu);
        fprintf(stderr,"  PSG=%llu FM=%llu/%llu bank2=%u DE63=%02X DE68=%02X\n",
                (unsigned long long)sound->psg_write_count,
                (unsigned long long)sound->fm_address_count,
                (unsigned long long)sound->fm_data_count,
                (unsigned)bus->mapped_bank[2],
                ys_sms_bus_read(bus,0xDE63),ys_sms_bus_read(bus,0xDE68));
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS first-frame bank-2 sound update: %llu instructions, PC=$%04X; PSG=22 FM=12 pairs\n",
           (unsigned long long)cpu.steps,cpu.pc);

    /* The original interrupt handler samples $DD. Idle $FF input bit4 is
       high, so the warm-reset branch at $013C must not be taken. */
    result=ys_z80_run_until(&cpu,0x0049,16);
    if (result!=Z80_RUNNING || cpu.pc!=0x0049 ||
        cpu.sp!=0xDFD6 || input.reads_dd!=1 ||
        ys_sms_bus_read(bus,0xC021)!=0 ||
        ys_sms_bus_read(bus,0xC10F)!=0 ||
        cpu.a!=1) {
        int code=fail("first VBlank handler IRQ return and wait release",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    result=ys_z80_run_until(&cpu,0x00C4,128);
    bool restored=result==Z80_RUNNING && cpu.pc==0x00C4 &&
        cpu.sp==initial_context.sp && cpu.iff1 && cpu.iff2 &&
        cpu.ei_delay==0 && bus->mapper_control==0x80 &&
        bus->mapped_bank[2]==2 &&
        cpu.a==initial_context.a && cpu.f==initial_context.f &&
        cpu.b==initial_context.b && cpu.c==initial_context.c &&
        cpu.d==initial_context.d && cpu.e==initial_context.e &&
        cpu.h==initial_context.h && cpu.l==initial_context.l &&
        cpu.a_alt==initial_context.a_alt &&
        cpu.f_alt==initial_context.f_alt &&
        cpu.b_alt==initial_context.b_alt &&
        cpu.c_alt==initial_context.c_alt &&
        cpu.d_alt==initial_context.d_alt &&
        cpu.e_alt==initial_context.e_alt &&
        cpu.h_alt==initial_context.h_alt &&
        cpu.l_alt==initial_context.l_alt &&
        cpu.ix==initial_context.ix && cpu.iy==initial_context.iy;
    if(!restored) {
        int code=fail("complete first VBlank ISR and restore startup context",&cpu);
        fprintf(stderr,"  SP=$%04X/$%04X AF=%02X%02X/%02X%02X IX=%04X/%04X IY=%04X/%04X\n",
                cpu.sp,initial_context.sp,
                cpu.a,cpu.f,initial_context.a,initial_context.f,
                cpu.ix,initial_context.ix,cpu.iy,initial_context.iy);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS first VBlank ISR return to original startup: %llu instructions, PC=$%04X SP=$%04X\n",
           (unsigned long long)cpu.steps,cpu.pc,cpu.sp);
    /* M25: execute the original dispatcher twice. First state $00 calls
       $00FC and installs $C01F=1; second state enters $0C4A, which calls
       $0A5B->$0A80->$0AE8 and the $0B10 32-byte work-RAM copy.
       Stop before $0B22 (tile-nibble transformation). */
    const uint8_t first_screen_value=ys_sms_bus_read(bus,0xC018);
    result=ys_z80_run_until(&cpu,0x00FC,24);
    if (result!=Z80_RUNNING || cpu.pc!=0x00FC ||
        cpu.sp!=0xDFEE || ys_sms_bus_read(bus,0xDFEE)!=0xD1 ||
        ys_sms_bus_read(bus,0xDFEF)!=0 ||
        ys_sms_bus_read(bus,0xC031)!=first_screen_value ||
        ys_sms_bus_read(bus,0xC01F)!=0) {
        int code=fail("first dispatcher state selects $00FC",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    result=ys_z80_run_until(&cpu,0x00C4,8);
    if (result!=Z80_RUNNING || cpu.sp!=0xDFF0 ||
        ys_sms_bus_read(bus,0xC01F)!=1) {
        int code=fail("first state initializes $C01F=1 and returns",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    result=ys_z80_run_until(&cpu,0x0C4A,24);
    if (result!=Z80_RUNNING || cpu.pc!=0x0C4A ||
        cpu.sp!=0xDFEE || ys_sms_bus_read(bus,0xDFEE)!=0xD1 ||
        ys_sms_bus_read(bus,0xDFEF)!=0 ||
        ys_sms_bus_read(bus,0xC01F)!=1) {
        int code=fail("second dispatcher state selects $0C4A",&cpu);
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    uint8_t copied_before[32];
    for(unsigned i=0;i<32;++i)
        copied_before[i]=ys_sms_bus_read(bus,(uint16_t)(0xC160u+i));
    result=ys_z80_run_until(&cpu,0x0B22,300);
    bool copy_ok=result==Z80_RUNNING && cpu.pc==0x0B22 &&
        cpu.sp==0xDFE6 && cpu.a==0 && cpu.b==0 && cpu.c==0 &&
        cpu.h==0xC1 && cpu.l==0x80 &&
        cpu.d==0xC5 && cpu.e==0x50 &&
        ys_sms_bus_read(bus,0xDFE6)==0xEF &&
        ys_sms_bus_read(bus,0xDFE7)==0x0A &&
        ys_sms_bus_read(bus,0xC01F)==1 &&
        vdp->register_writes==15 && vdp->vram_writes==192 &&
        sound->psg_write_count==22 && sound->fm_data_count==12;
    for(unsigned i=0;i<32;++i)
        copy_ok=copy_ok && ys_sms_bus_read(bus,(uint16_t)(0xC530u+i))==
                           copied_before[i];
    if(!copy_ok) {
        int code=fail("second-state $0B10 sprite-palette staging copy",&cpu);
        fprintf(stderr,"  SP=%04X HL=%02X%02X DE=%02X%02X BC=%02X%02X state=%02X\n",
                cpu.sp,cpu.h,cpu.l,cpu.d,cpu.e,cpu.b,cpu.c,
                ys_sms_bus_read(bus,0xC01F));
        free(rom);free(bus);free(vdp);free(sound);return code;
    }
    printf("PASS main dispatcher state 0->$00FC, state 1->$0C4A: %llu instructions\n",
           (unsigned long long)cpu.steps);
    puts("PASS second-state $0B10 32-byte WRAM staging copy; PC=$0B22, SP=$DFE6");
    puts("Stop before RLD palette nibble loop $0B22; no frame scheduler.");
    if(argc==4) {
        uint8_t *pixels=malloc(YS_SMS_RGB_BYTES);
        if(!pixels) {
            fputs("could not allocate native VDP frame\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        YsSmsFrameStats stats;
        bool rendered=ys_sms_video_render(vdp,pixels,YS_SMS_RGB_BYTES,&stats);
        FILE *snapshot=rendered?fopen(argv[3],"wb"):NULL;
        if(!snapshot) rendered=false;
        if(rendered && !ys_sms_video_write_ppm(snapshot,pixels,YS_SMS_RGB_BYTES))
            rendered=false;
        if(snapshot && fclose(snapshot)!=0) rendered=false;
        free(pixels);
        if(!rendered) {
            fputs("could not write source-ROM VDP snapshot\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        printf("Wrote real state snapshot at PC=$0B22: %s (PPM 256x192; not a completed title screen)\n",
               argv[3]);
        printf("Snapshot sprite-overflow lines=%u collision pixels=%u (render-only diagnostics)\n",
               stats.sprite_overflow_lines,stats.sprite_collision_pixels);
    }
    free(rom);free(bus);free(vdp);free(sound);
    return EXIT_SUCCESS;
}
