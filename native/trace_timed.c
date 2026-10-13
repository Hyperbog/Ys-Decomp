/* M30 original-ROM reset through TWO clock-generated VBlank IM1 events,
   including legitimate immediate re-entry and a stable return to $0764.
   This is a bounded diagnostic, never interactive gameplay. No injected IRQ. */
#include "sms_runtime.h"
#include "sms_video.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fail(const char *message, const YsSmsRuntime *rt) {
    const YsZ80 *cpu=rt->cpu;
    fprintf(stderr,"FAIL timed source-ROM %s: steps=%llu PC=$%04X"
            " fault=$%04X SP=$%04X status=%s lastT=%u"
            " totalT=%llu line=%u hpos=%u frames=%llu"
            " VBlank=%llu IRQ=%llu VDPstatus=%02X reg1=%02X\n",
            message,(unsigned long long)cpu->steps,cpu->pc,cpu->fault_pc,
            cpu->sp,ys_z80_status_name(cpu->status),cpu->last_tstates,
            (unsigned long long)cpu->total_tstates,rt->clock.line,
            rt->clock.tstates,(unsigned long long)rt->clock.frames,
            (unsigned long long)rt->clock.vblank_events,
            (unsigned long long)rt->recognized_irqs,
            cpu->vdp->status,cpu->vdp->registers[1]);
    return EXIT_FAILURE;
}

/* Compare architectural registers, not PC, IRQ state or step counters. */
static bool same_registers(const YsZ80 *a, const YsZ80 *b) {
    return a->a==b->a && a->f==b->f &&
        a->b==b->b && a->c==b->c && a->d==b->d && a->e==b->e &&
        a->h==b->h && a->l==b->l &&
        a->a_alt==b->a_alt && a->f_alt==b->f_alt &&
        a->b_alt==b->b_alt && a->c_alt==b->c_alt &&
        a->d_alt==b->d_alt && a->e_alt==b->e_alt &&
        a->h_alt==b->h_alt && a->l_alt==b->l_alt &&
        a->ix==b->ix && a->iy==b->iy;
}

/* Independent host-side reference for Ys bank-0 $0695-$06C0.
   Four interleaved VRAM rows, with signed RLE commands:
   bit7=0 repeats the following byte, bit7=1 copies that many
   literal bytes; zero terminates each row. This decoder does not
   call the Z80 interpreter or mutate its bus/VDP, and rejects
   crossing the mapped 16 KiB cartridge window or VRAM bounds. */
static bool reference_pattern_rows(const YsSmsBus *bus,
                                   uint8_t expected[YS_VRAM_BYTES],
                                   uint8_t touched[YS_VRAM_BYTES],
                                   size_t *written, uint16_t *end_hl) {
    uint16_t hl=0x8000u;
    size_t count=0u;
    memset(expected,0,YS_VRAM_BYTES);
    memset(touched,0,YS_VRAM_BYTES);
    for(unsigned row=0;row<4u;++row) {
        unsigned offset=row;
        bool terminated=false;
        for(unsigned command=0;command<1024u;++command) {
            if(hl>=0xC000u) return false;
            uint8_t header=ys_sms_bus_read(bus,hl++);
            if(header==0u) {terminated=true;break;}
            unsigned length=header&0x7Fu;
            if(length==0u) length=256u; /* B=0 / DJNZ wraps. */
            bool literal=(header&0x80u)!=0u;
            if((unsigned)hl+ (literal?length:1u)>0xC000u)
                return false;
            for(unsigned i=0;i<length;++i) {
                if(offset>=YS_VRAM_BYTES) return false;
                uint8_t value=ys_sms_bus_read(
                    bus,(uint16_t)(hl+(literal?i:0u)));
                expected[offset]=value;
                touched[offset]=1u;
                ++count;
                offset+=4u;
            }
            hl=(uint16_t)(hl+(literal?length:1u));
        }
        if(!terminated) return false;
    }
    *written=count;
    *end_hl=hl;
    return count>0u;
}

/* Independent, bounded host reference for the original bank-0
   $0C20 RLE/sequence decoder. The Z80 interpreter independently
   executes the source routine and its output is compared bytewise.
   Signed opcode: negative = copy N literal bytes; positive = write
   N incrementing bytes. Zero terminates the stream. */
static bool reference_bank5_decode(const uint8_t *rom,
                                   uint8_t *output, size_t capacity,
                                   size_t *length, size_t *consumed) {
    const size_t base=5u*YS_ROM_BANK_BYTES+0x361Au;
    const size_t limit=6u*YS_ROM_BANK_BYTES;
    size_t at=base, used=0;
    for(unsigned commands=0; commands<4096u && at<limit; ++commands) {
        uint8_t opcode=rom[at++];
        if(opcode==0u) {
            *length=used;
            *consumed=at-base;
            return used!=0u;
        }
        unsigned count=(opcode&0x80u) ?
            (opcode&0x7Fu ? opcode&0x7Fu : 256u) : opcode;
        if(used+count>capacity) return false;
        if(opcode&0x80u) {
            if(at+count>limit) return false;
            for(unsigned i=0;i<count;++i) output[used++]=rom[at++];
        } else {
            if(at>=limit) return false;
            uint8_t first=rom[at++];
            for(unsigned i=0;i<count;++i)
                output[used++]=(uint8_t)(first+i);
        }
    }
    return false;
}


/* Independent reference model for source bank-0 $0BEF-$0C1F's
   two interleaved resource rows. Command 0 terminates one row,
   0x80..0xFF copies N literal bytes, 1..127 repeats one value N
   times; each output step advances by C=2. The Z80 CPU still
   executes all source instructions; this model only checks output. */
static bool reference_staged_rows(const uint8_t *source,size_t size,
                                  uint8_t *expected,size_t capacity,
                                  size_t *consumed,size_t *written) {
    size_t at=0u,writes=0u;
    if(!source || !expected || !consumed || !written || capacity<2u)
        return false;
    for(unsigned row=0u;row<2u;++row) {
        size_t dest=row;
        bool terminated=false;
        for(unsigned commands=0u;commands<2048u && at<size;++commands) {
            uint8_t cmd=source[at++];
            if(cmd==0u) {terminated=true;break;}
            unsigned n=(cmd&0x80u) ? (cmd&0x7Fu) : cmd;
            if(n==0u) n=256u; /* actual Z80 DJNZ wrap */
            if(cmd&0x80u) {
                if(at+n>size) return false;
                for(unsigned i=0u;i<n;++i) {
                    if(dest>=capacity) return false;
                    expected[dest]=source[at++];
                    dest+=2u;++writes;
                }
            } else {
                if(at>=size) return false;
                uint8_t repeated=source[at++];
                for(unsigned i=0u;i<n;++i) {
                    if(dest>=capacity) return false;
                    expected[dest]=repeated;
                    dest+=2u;++writes;
                }
            }
        }
        if(!terminated) return false;
    }
    *consumed=at;*written=writes;
    return writes>0u;
}

int main(int argc,char **argv) {
    if (!(argc==2 || (argc==4 && strcmp(argv[2],"--frame")==0))) {
        fputs("usage: ys-native-timed-rom user-supplied-Ys.sms [--frame snapshot.ppm]\n"
              "Stops after original staged tile/resource transform $0C72 (no gameplay).\n",
              stderr);
        return EXIT_FAILURE;
    }
    FILE *in=fopen(argv[1],"rb");
    if(!in) {perror("open ROM");return EXIT_FAILURE;}
    uint8_t *rom=malloc(YS_ROM_BYTES);
    YsSmsBus *bus=malloc(sizeof(*bus));
    YsSmsVdp *vdp=malloc(sizeof(*vdp));
    YsSmsSound *sound=malloc(sizeof(*sound));
    if(!rom || !bus || !vdp || !sound) {
        fclose(in);free(rom);free(bus);free(vdp);free(sound);
        return EXIT_FAILURE;
    }
    size_t size=fread(rom,1,YS_ROM_BYTES,in);
    int extra=fgetc(in);
    fclose(in);
    if(size!=YS_ROM_BYTES || extra!=EOF ||
       memcmp(rom+0x7FF0,"TMR SEGA",8)!=0 ||
       !ys_sms_bus_init(bus,rom,size)) {
        fputs("invalid ROM size or SMS header; this tool does not ship ROMs\n",stderr);
        free(rom);free(bus);free(vdp);free(sound);
        return EXIT_FAILURE;
    }
    ys_sms_vdp_reset(vdp);
    ys_sms_sound_reset(sound);
    YsSmsInput input;
    ys_sms_input_reset(&input);
    YsZ80 cpu;
    ys_z80_reset(&cpu,bus);
    ys_z80_attach_vdp(&cpu,vdp);
    ys_z80_attach_sound(&cpu,sound);
    ys_z80_attach_input(&cpu,&input);
    YsSmsRuntime runtime;
    if(!ys_sms_runtime_bind(&runtime,&cpu,YS_SMS_NTSC)) {
        free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
    }
    unsigned long iterations=0;
    while(runtime.recognized_irqs==0u && iterations<1000000ul) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING && status!=Z80_HALTED) {
            int result=fail("CPU stopped before first automatic IRQ",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++iterations;
    }
    if(runtime.recognized_irqs!=1u || cpu.pc!=0x0038u ||
       cpu.interrupt_mode!=1u || cpu.iff1 ||
       runtime.clock.vblank_events==0u ||
       (vdp->status&0x80u)==0u ||
       (vdp->registers[1]&0x20u)==0u ||
       cpu.total_tstates<YS_SMS_VISIBLE_LINES*YS_SMS_TSTATES_PER_LINE ||
       cpu.sp<0xC000u || cpu.sp>0xFFFDu) {
        int result=fail("first real timed VBlank IRQ not at source vector",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    const YsZ80 interrupted=cpu;
    const uint8_t control_before=bus->mapper_control;
    const uint8_t slot2_before=bus->mapped_bank[2];
    uint16_t saved=(uint16_t)((uint16_t)ys_sms_bus_read(bus,cpu.sp) |
                     ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(cpu.sp+1u))<<8));
    /* At $0038 the source code PUSH AF precedes IN A,($BF). Run it,
       then verify the actual status-port read consumes the VBlank bit. */
    if(ys_sms_runtime_step_auto(&runtime)!=Z80_RUNNING ||
       cpu.pc!=0x0039u ||
       ys_sms_runtime_step_auto(&runtime)!=Z80_RUNNING ||
       cpu.pc!=0x003Bu ||
       (cpu.a&0x80u)==0u || (vdp->status&0x80u)!=0u ||
       runtime.recognized_irqs!=1u) {
        int result=fail("real $0038 ISR failed to acknowledge VBlank",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed actual Ys reset to first IM1: instructions=%llu"
           " T-states=%llu VBlank=%llu IRQ=%llu savedPC=$%04X"
           " PC=$%04X SP=$%04X\n",
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)runtime.recognized_irqs,
           saved,cpu.pc,cpu.sp);
    puts("No injected IRQ; source ISR status acknowledgment verified.");
    puts("M29 timed ISR status acknowledgment at PC=$003B verified.");
    /* M30: continue this SAME clock-generated interrupt through the
       source zero-state branch $0102->$0148, the real bank-2 $8000
       sound update and the register/mapper restore at $0194-$01AB.
       No injection, timing reset, stack patch or artificial return. */
    unsigned long handler_steps=0;
    while(cpu.pc!=saved && handler_steps<4000ul &&
          runtime.recognized_irqs==1u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("first zero-state ISR stopped before return",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++handler_steps;
    }
    /* At this phase of cold boot, a sixth VBlank becomes pending *during*
       the first sound update.  The original $01AA EI / $01AB RET
       restores the interrupted $0764 context; the pending IM1 is then
       recognized immediately at the RET boundary.  Do not suppress it. */
    bool bounced=saved==0x0764u && cpu.pc==0x0038u &&
        handler_steps>20u && runtime.recognized_irqs==2u &&
        runtime.clock.vblank_events==6u &&
        cpu.sp==interrupted.sp && !cpu.iff1 &&
        cpu.iff2 && (vdp->status&0x80u)!=0u &&
        same_registers(&cpu,&interrupted) &&
        bus->mapper_control==control_before &&
        bus->mapped_bank[2]==slot2_before &&
        ys_sms_bus_read(bus,0xC021u)==0u &&
        ys_sms_bus_read(bus,0xC10Fu)==1u &&
        (uint16_t)((uint16_t)ys_sms_bus_read(bus,cpu.sp) |
           ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(cpu.sp+1u))<<8))==saved;
    if(!bounced) {
        int result=fail("first ISR return and legitimate second VBlank re-entry",&runtime);
        fprintf(stderr,"  expected return=$%04X IRQ=2 VBlank=6"
                       " regs=%s mapper=%02X/%02X bank2=%u/%u C10F=%02X\n",
                saved,same_registers(&cpu,&interrupted)?"restored":"different",
                bus->mapper_control,control_before,bus->mapped_bank[2],
                slot2_before,ys_sms_bus_read(bus,0xC10Fu));
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS natural second VBlank re-entry after $01AB RET:"
           " PC=$0038 savedPC=$%04X VBlank=%llu IRQ=%llu"
           " handler_steps=%lu\n",saved,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)runtime.recognized_irqs,handler_steps);

    /* The sixth VBlank is cleared by the next genuine ISR read. With
       no seventh VBlank pending, the second ISR can fully RET to $0764.
       This is the first stable original startup resume in the timed path. */
    unsigned long second_handler_steps=0;
    while(cpu.pc!=saved && second_handler_steps<4000ul &&
          runtime.recognized_irqs==2u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("second timed ISR stopped before stable return",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++second_handler_steps;
    }
    bool registers_restored=same_registers(&cpu,&interrupted);
    bool returned=bounced && registers_restored &&
        cpu.pc==saved && second_handler_steps>20u &&
        cpu.sp==(uint16_t)(interrupted.sp+2u) &&
        cpu.iff1 && cpu.iff2 && cpu.ei_delay==0u &&
        bus->mapper_control==control_before &&
        bus->mapped_bank[2]==slot2_before &&
        ys_sms_bus_read(bus,0xC021u)==0u &&
        ys_sms_bus_read(bus,0xC10Fu)==1u &&
        vdp->status==0u && runtime.recognized_irqs==2u &&
        runtime.clock.vblank_events==6u;
    if(!returned) {
        int result=fail("source zero-state ISR context/mapper restoration",&runtime);
        fprintf(stderr,"  expected PC=$%04X SP=$%04X mapper=%02X bank2=%u"
                       " AF=%02X%02X/%02X%02X C021=%02X C10F=%02X"
                       " shadow=%s steps=%lu\n",
                saved,(uint16_t)(interrupted.sp+2u),control_before,
                slot2_before,cpu.a,cpu.f,interrupted.a,interrupted.f,
                ys_sms_bus_read(bus,0xC021u),ys_sms_bus_read(bus,0xC10Fu),
                registers_restored?"restored":"different",handler_steps);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed Ys second zero-state ISR stable return to $%04X:"
           " first_steps=%lu second_steps=%lu"
           " total_steps=%llu T-states=%llu SP=$%04X"
           " mapper=%02X bank2=%u IRQ=%llu\n",
           saved,handler_steps,second_handler_steps,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,cpu.sp,
           bus->mapper_control,bus->mapped_bank[2],
           (unsigned long long)runtime.recognized_irqs);
    puts("PASS M30 timed two-ISR return; resume original startup at $0764.");

    /* M32: finish original bank-0 VDP initializer $0764/$0765/$0767.
       This is POP AF, OUT ($BE),A, RET to the cold-boot CALL $0749
       successor $00C1. No CPU patch, synthetic IRQ or clock reset. */
    unsigned resumed_steps=0;
    while(cpu.pc!=0x00C1u && resumed_steps<8u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("VDP initializer continuation unsupported",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++resumed_steps;
    }
    if(cpu.pc!=0x00C1u || resumed_steps!=3u ||
       cpu.sp!=0xDFF0u || cpu.last_tstates!=10u ||
       runtime.recognized_irqs!=2u ||
       bus->mapped_bank[2]!=2u) {
        int result=fail("source $0764 POP AF/OUT/RET to $00C1",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS natural Ys VDP initializer completed to $00C1:"
           " steps=%llu T-states=%llu SP=$%04X VDPwrites=%llu IRQ=%llu\n",
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,cpu.sp,
           (unsigned long long)vdp->vram_writes,
           (unsigned long long)runtime.recognized_irqs);

    /* Enter the *original* VBlank wait bridge $0BC5 -> $0042.
       Stop at the source's $0046 LD A,($C021) after its EI. Later
       frame dispatch remains a separate source-backed checkpoint. */
    unsigned wait_steps=0u;
    while(cpu.pc!=0x0046u && wait_steps<128u &&
          runtime.recognized_irqs==2u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("original VBlank wait bridge unsupported",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++wait_steps;
    }
    if(cpu.pc!=0x0046u || wait_steps<8u ||
       ys_sms_bus_read(bus,0xC021u)!=1u ||
       !cpu.iff1 || cpu.ei_delay!=1u ||
       runtime.recognized_irqs!=2u ||
       bus->mapped_bank[2]!=2u) {
        int result=fail("source $0BC5 -> $0042 wait-loop EI checkpoint",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed Ys first original frame-wait entry:"
           " PC=$%04X SP=$%04X C021=%02X IRQ=%llu"
           " VBlank=%llu steps=%llu T-states=%llu\n",
           cpu.pc,cpu.sp,ys_sms_bus_read(bus,0xC021u),
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates);
    /* M33: the source's $0046/$0049/$004A busy-wait must advance the
       instruction clock until the NEXT VBlank arrives. The frame handler
       clears $C021 and returns into the interrupted poll. $0BC5 then
       restores the saved register context and RETs to startup $00C4.
       No VDP/status injection, PC edit, synthetic stack/IRQ or host input. */
    const YsZ80 startup_at_wait=cpu;
    const uint64_t irq_before_wait=runtime.recognized_irqs;
    const uint64_t vblank_before_wait=runtime.clock.vblank_events;
    const uint64_t vram_before_wait=vdp->vram_writes;
    const uint64_t psg_before_wait=sound->psg_write_count;
    bool captured_wait_irq=false;
    uint16_t wait_irq_pc=0;
    uint16_t wait_irq_sp=0;
    unsigned long wait_iterations=0;
    while(cpu.pc!=0x00C4u && wait_iterations<90000ul) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("source $0046 wait or first natural frame ISR stopped",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++wait_iterations;
        if(!captured_wait_irq &&
           runtime.recognized_irqs>irq_before_wait) {
            if(runtime.recognized_irqs!=irq_before_wait+1u ||
               cpu.pc!=0x0038u || !(vdp->status&0x80u)) {
                int result=fail("source first frame-wait IM1 entry",&runtime);
                free(rom);free(bus);free(vdp);free(sound);return result;
            }
            captured_wait_irq=true;
            wait_irq_sp=cpu.sp;
            wait_irq_pc=(uint16_t)(
                (uint16_t)ys_sms_bus_read(bus,cpu.sp) |
                ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(cpu.sp+1u))<<8));
            if(wait_irq_pc<0x0046u || wait_irq_pc>0x004Cu) {
                int result=fail("frame-wait interrupt PC outside source loop",&runtime);
                fprintf(stderr,"  suspended source PC=$%04X\n",wait_irq_pc);
                free(rom);free(bus);free(vdp);free(sound);return result;
            }
            printf("PASS natural frame-wait VBlank entry:"
                   " IRQ=%llu VBlank=%llu suspendedPC=$%04X"
                   " SP=$%04X CPUsteps=%llu\n",
                   (unsigned long long)runtime.recognized_irqs,
                   (unsigned long long)runtime.clock.vblank_events,
                   wait_irq_pc,wait_irq_sp,
                   (unsigned long long)cpu.steps);
        }
        if(runtime.recognized_irqs>irq_before_wait+2u) {
            int result=fail("unexpected multiple nested frame-wait IRQs",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
    }
    bool frame_wait_done=captured_wait_irq &&
        cpu.pc==0x00C4u && cpu.sp==0xDFF0u &&
        cpu.status==Z80_RUNNING &&
        ys_sms_bus_read(bus,0xC021u)==0u &&
        ys_sms_bus_read(bus,0xC10Fu)==0u &&
        runtime.recognized_irqs>=irq_before_wait+1u &&
        runtime.clock.vblank_events>vblank_before_wait &&
        vdp->vram_writes>vram_before_wait &&
        sound->psg_write_count>psg_before_wait &&
        bus->mapped_bank[2]==2u &&
        cpu.ix==startup_at_wait.ix && cpu.iy==startup_at_wait.iy;
    if(!frame_wait_done) {
        int result=fail("first original frame wait and source ISR completion",&runtime);
        fprintf(stderr,"  suspendedPC=$%04X waitsteps=%lu C021=%02X"
                " C10F=%02X VRAM=%llu->%llu PSG=%llu->%llu\n",
                wait_irq_pc,wait_iterations,
                ys_sms_bus_read(bus,0xC021u),
                ys_sms_bus_read(bus,0xC10Fu),
                (unsigned long long)vram_before_wait,
                (unsigned long long)vdp->vram_writes,
                (unsigned long long)psg_before_wait,
                (unsigned long long)sound->psg_write_count);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys frame-wait completed to $00C4:"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu"
           " VRAMwrites=%llu PSGwrites=%llu waitsteps=%lu"
           " suspendedPC=$%04X\n",
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)vdp->vram_writes,
           (unsigned long long)sound->psg_write_count,
           wait_iterations,wait_irq_pc);
    puts("M33 original frame-wait complete; continue to M34 dispatcher.");

    /* M34: run the authentic reset dispatcher through state zero and into
       state one, then through the early $0C4A -> $0A5B -> $0A80
       -> $0AE8 palette staging path. Execute the 32-byte, source-backed
       $0B22 RLD nibble processing loop and stop at the first
       $0AF6 timed frame-wait CALL, before initiating a new wait.
       No host-injected IRQ, patched RAM, forced PC or palette bytes. */
    unsigned long dispatch_steps=0;
    while(cpu.pc!=0x0C4Au && dispatch_steps<96u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M34 source reset dispatch stopped",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++dispatch_steps;
    }
    if(cpu.pc!=0x0C4Au || dispatch_steps<6u ||
       ys_sms_bus_read(bus,0xC01Fu)!=1u ||
       cpu.sp!=0xDFEEu ||
       bus->mapped_bank[2]!=2u ||
       runtime.recognized_irqs!=3u) {
        int result=fail("M34 source dispatcher selects state 1 $0C4A",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed Ys state 0 -> 1 dispatch: PC=$0C4A"
           " steps=%llu SP=$%04X C01F=%02X IRQ=%llu\n",
           (unsigned long long)cpu.steps,cpu.sp,
           ys_sms_bus_read(bus,0xC01Fu),
           (unsigned long long)runtime.recognized_irqs);

    uint8_t initial_palette[32];
    for(unsigned i=0;i<32u;++i)
        initial_palette[i]=ys_sms_bus_read(bus,(uint16_t)(0xC160u+i));
    unsigned long staging_steps=0;
    while(cpu.pc!=0x0B22u && staging_steps<2000u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M34 source palette staging stopped",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++staging_steps;
    }
    bool staged=cpu.pc==0x0B22u && staging_steps>10u &&
        cpu.sp==0xDFE6u && cpu.a==0u &&
        cpu.h==0xC1u && cpu.l==0x80u &&
        cpu.b==0u && cpu.c==0u &&
        bus->mapped_bank[2]==2u &&
        runtime.recognized_irqs==3u;
    for(unsigned i=0;i<32u;++i)
        staged=staged &&
            ys_sms_bus_read(bus,(uint16_t)(0xC530u+i))==initial_palette[i];
    if(!staged) {
        int result=fail("M34 source $0B10 staging to $0B22",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed Ys palette staging: PC=$0B22"
           " steps=%llu T-states=%llu SP=$%04X\n",
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,cpu.sp);

    unsigned long palette_steps=0;
    while(cpu.pc!=0x0AF6u && palette_steps<2500u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M34 authentic 32-byte RLD palette transform stopped",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++palette_steps;
    }
    if(cpu.pc!=0x0AF6u || palette_steps<450u ||
       cpu.a!=0u || cpu.b!=3u ||
       cpu.h!=0xC0u || cpu.l!=0x2Cu ||
       ys_sms_bus_read(bus,0xC02Cu)!=1u ||
       ys_sms_bus_read(bus,0xC021u)!=0u ||
       runtime.recognized_irqs!=3u ||
       runtime.clock.vblank_events!=7u) {
        int result=fail("M34 palette nibble loop/first delay checkpoint $0AF6",&runtime);
        fprintf(stderr,"  palette_steps=%lu HL=%02X%02X BC=%02X%02X"
                " C02C=%02X\n",palette_steps,cpu.h,cpu.l,
                cpu.b,cpu.c,ys_sms_bus_read(bus,0xC02Cu));
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed Ys first palette nibble transform:"
           " PC=$0AF6 steps=%llu T-states=%llu"
           " palette_steps=%lu IRQ=%llu VBlank=%llu\n",
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,palette_steps,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events);
    puts("M34 palette pass zero verified; M35 continues real frame delays.");
    /* Original source $0AF6-$0AFE runs 3 IRQ-driven waits for each
       of four palette levels (A=0,1,2,3). Stop at $0B00 before
       the bank-7 transfer. NO synthetic VBlank/stack/PC changes.
       Require actual $0042 frame polling to clear its own flag. */
    const uint16_t palette_saved_sp=cpu.sp;
    const uint8_t mapper_saved=bus->mapper_control;
    const uint8_t bank_saved=bus->mapped_bank[2];
    const uint64_t before_wait_vblank=runtime.clock.vblank_events;
    const uint64_t before_wait_irqs=runtime.recognized_irqs;
    const uint64_t before_wait_vram=vdp->vram_writes;
    const uint64_t before_wait_psg=sound->psg_write_count;
    const uint16_t saved_ix=cpu.ix,saved_iy=cpu.iy;
    unsigned long frame_wait_steps=0u;
    unsigned frame_returns=0u;
    unsigned palette_passes=1u; /* pass 0 transform completed by M34 */
    unsigned frame_wakeups=0u;
    uint64_t last_irq=runtime.recognized_irqs;
    uint64_t last_vblank=runtime.clock.vblank_events;
    bool invalid_wait=false;
    while(cpu.pc!=0x0B00u && frame_wait_steps<300000u) {
        uint16_t prior_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M35 source palette delay unsupported",&runtime);
            fprintf(stderr,"  priorPC=$%04X palette_pass=%u frame_returns=%u\n",
                    prior_pc,palette_passes,frame_returns);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++frame_wait_steps;
        if(runtime.recognized_irqs!=last_irq) {
            if(runtime.recognized_irqs!=last_irq+1u ||
               cpu.pc!=0x0038u || !(vdp->status&0x80u))
                invalid_wait=true;
            ++frame_wakeups;
            last_irq=runtime.recognized_irqs;
        }
        if(runtime.clock.vblank_events!=last_vblank) {
            if(runtime.clock.vblank_events!=last_vblank+1u)
                invalid_wait=true;
            last_vblank=runtime.clock.vblank_events;
        }
        if(prior_pc==0x0AF6u && cpu.pc==0x0BC5u) {
            /* The source calls the original register-preserving
               $0BC5 wait bridge; do not substitute host delays. */
            if(cpu.sp!=(uint16_t)(palette_saved_sp-2u))
                invalid_wait=true;
        }
        if(prior_pc==0x0B4Du && cpu.pc==0x0AEFu) {
            ++palette_passes;
            if(palette_passes>4u) invalid_wait=true;
        }
        if(cpu.pc==0x0AF9u && prior_pc==0x0BEEu) {
            ++frame_returns;
            if(frame_returns>12u ||
               cpu.sp!=palette_saved_sp ||
               ys_sms_bus_read(bus,0xC021u)!=0u ||
               bus->mapper_control!=mapper_saved ||
               bus->mapped_bank[2]!=bank_saved ||
               cpu.ix!=saved_ix || cpu.iy!=saved_iy)
                invalid_wait=true;
        }
        if(invalid_wait) {
            int result=fail("M35 palette wait IRQ/stack/mapper invariant",&runtime);
            fprintf(stderr,"  priorPC=$%04X waits=%u passes=%u"
                    " irq=%llu vblank=%llu\n",prior_pc,frame_returns,
                    palette_passes,
                    (unsigned long long)runtime.recognized_irqs,
                    (unsigned long long)runtime.clock.vblank_events);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
    }
    if(cpu.pc!=0x0B00u || frame_returns!=12u ||
       palette_passes!=4u || cpu.a!=4u ||
       cpu.b!=0u || cpu.sp!=palette_saved_sp ||
       cpu.ix!=saved_ix || cpu.iy!=saved_iy ||
       runtime.recognized_irqs<=before_wait_irqs ||
       runtime.clock.vblank_events<=before_wait_vblank ||
       vdp->vram_writes<=before_wait_vram ||
       sound->psg_write_count<=before_wait_psg ||
       bus->mapped_bank[2]!=bank_saved ||
       bus->mapper_control!=mapper_saved ||
       ys_sms_bus_read(bus,0xC021u)!=0u ||
       ys_sms_bus_read(bus,0xC02Cu)!=0u) {
        int result=fail("M35 original 4-level palette fade completion",&runtime);
        fprintf(stderr,"  waits=%u passes=%u wakeups=%u"
                " steps=%lu A=%02X B=%02X C021=%02X C02C=%02X\n",
                frame_returns,palette_passes,frame_wakeups,
                frame_wait_steps,cpu.a,cpu.b,
                ys_sms_bus_read(bus,0xC021u),
                ys_sms_bus_read(bus,0xC02Cu));
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS timed Ys four-level palette fade to $0B00:"
           " waits=%u palette_passes=%u wakeups=%u"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu"
           " VRAMwrites=%llu PSGwrites=%llu\n",
           frame_returns,palette_passes,frame_wakeups,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)vdp->vram_writes,
           (unsigned long long)sound->psg_write_count);
    puts("M35 palette delay complete; M36 now executes bank-7 data and VDP setup.");
    /* M36: source $0B00 loads MapperSlot2=7 and copies 16 bytes from
       bank 7 $B9C3 to WRAM $C170 through LDI ($0B19-$0B21).
       The return at $0A83 resumes initial VDP register setup,
       tail-calling $0762 to write sprite Y terminator before
       returning to caller $0A5E. No memory, PC or IRQ injection. */
    const uint16_t transfer_initial_sp=cpu.sp;
    const uint64_t before_transfer_irqs=runtime.recognized_irqs;
    const uint64_t before_transfer_vblanks=runtime.clock.vblank_events;
    const uint64_t before_transfer_vram=vdp->vram_writes;
    const uint64_t before_transfer_cram=vdp->cram_writes;
    const uint64_t before_transfer_registers=vdp->register_writes;
    uint8_t bank7_expected[16];
    uint8_t staged_before[16];
    for (unsigned i=0;i<16u;++i) {
        bank7_expected[i]=rom[7u*YS_ROM_BANK_BYTES+0x39C3u+i];
        staged_before[i]=ys_sms_bus_read(bus,(uint16_t)(0xC170u+i));
    }
    unsigned transfer_steps=0;
    bool mapped_bank7=false;
    unsigned ldi_count=0;
    while(cpu.pc!=0x0A83u && transfer_steps<160u) {
        const uint16_t prior_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M36 authentic bank-7 data copy unsupported",&runtime);
            fprintf(stderr,"  priorPC=$%04X transfer_steps=%u\n",
                    prior_pc,transfer_steps);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++transfer_steps;
        if (prior_pc==0x0B02u && cpu.pc==0x0B05u)
            mapped_bank7=bus->mapped_bank[2]==7u &&
                         bus->bank_select[2]==7u;
        if (prior_pc==0x0B1Au && cpu.pc==0x0B1Cu)
            ++ldi_count;
        if (runtime.recognized_irqs!=before_transfer_irqs)
            break;
    }
    bool transfer_ok=cpu.pc==0x0A83u &&
        transfer_steps>60u && transfer_steps<160u &&
        mapped_bank7 && ldi_count==16u &&
        cpu.sp==(uint16_t)(transfer_initial_sp+2u) &&
        cpu.h==0xB9u && cpu.l==0xD3u &&
        cpu.d==0xC1u && cpu.e==0x80u &&
        cpu.b==0u && cpu.c==0u && cpu.a==7u &&
        bus->mapped_bank[2]==7u &&
        runtime.recognized_irqs==before_transfer_irqs &&
        runtime.clock.vblank_events==before_transfer_vblanks &&
        vdp->vram_writes==before_transfer_vram &&
        vdp->cram_writes==before_transfer_cram;
    unsigned bytes_changed=0;
    for (unsigned i=0;i<16u;++i) {
        const uint8_t actual=ys_sms_bus_read(bus,(uint16_t)(0xC170u+i));
        transfer_ok=transfer_ok && actual==bank7_expected[i];
        if (actual!=staged_before[i]) ++bytes_changed;
    }
    if(!transfer_ok || bytes_changed==0u) {
        int result=fail("M36 bank-7 source LDI bytes or mapper mismatch",&runtime);
        fprintf(stderr,"  transfer=%u ldi=%u changed=%u"
                " mapper=%02X bank2=%u HL=%02X%02X DE=%02X%02X\n",
                transfer_steps,ldi_count,bytes_changed,
                bus->mapper_control,bus->mapped_bank[2],
                cpu.h,cpu.l,cpu.d,cpu.e);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys bank-7 source transfer: PC=$0A83"
           " bank2=%u LDI=%u bytes_changed=%u"
           " steps=%llu T-states=%llu IRQ=%llu\n",
           bus->mapped_bank[2],ldi_count,bytes_changed,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs);

    /* Bank-0 $0A83-$0AA4 programs registers 0/1 using source RST $28,
       writes $D0 to the sprite Y terminator through $0762, and
       returns to the unfinished graphics init at $0A5E. */
    unsigned vdp_setup_steps=0;
    while(cpu.pc!=0x0A5Eu && vdp_setup_steps<110u &&
          runtime.recognized_irqs==before_transfer_irqs) {
        const uint16_t prior_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M36 source VDP register setup unsupported",&runtime);
            fprintf(stderr,"  priorPC=$%04X setup_steps=%u\n",
                    prior_pc,vdp_setup_steps);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++vdp_setup_steps;
    }
    bool vdp_setup_ok=cpu.pc==0x0A5Eu &&
        cpu.sp==(uint16_t)(transfer_initial_sp+4u) &&
        vdp_setup_steps>20u && vdp_setup_steps<110u &&
        vdp->register_writes>=before_transfer_registers+2u &&
        vdp->registers[0]==ys_sms_bus_read(bus,0xC010u) &&
        vdp->registers[1]==ys_sms_bus_read(bus,0xC011u) &&
        vdp->vram[0x3F00u]==0xD0u &&
        vdp->vram_writes==before_transfer_vram+1u &&
        vdp->cram_writes==before_transfer_cram &&
        bus->mapped_bank[2]==7u &&
        runtime.recognized_irqs==before_transfer_irqs &&
        runtime.clock.vblank_events==before_transfer_vblanks;
    if(!vdp_setup_ok) {
        int result=fail("M36 source VDP registers / sprite Y terminator",&runtime);
        fprintf(stderr,"  VDPsteps=%u SP=$%04X R0=%02X/%02X"
                " R1=%02X/%02X Y=%02X writes=%llu->%llu\n",
                vdp_setup_steps,cpu.sp,
                vdp->registers[0],ys_sms_bus_read(bus,0xC010u),
                vdp->registers[1],ys_sms_bus_read(bus,0xC011u),
                vdp->vram[0x3F00u],
                (unsigned long long)before_transfer_vram,
                (unsigned long long)vdp->vram_writes);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS authentic Ys VDP init return: PC=$0A5E"
           " R0=$%02X R1=$%02X spriteY[0]=$%02X"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu\n",
           vdp->registers[0],vdp->registers[1],
           vdp->vram[0x3F00u],
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events);
    puts("M36 verified bank-7/VDP register setup; resume at $0A5E.");

    /* M37 source $0A5E-$0A76: program VDP scroll registers 8/9,
       clear the source video scroll fields at $C018/$C019, and
       execute CALL $06D4 with BC=$0020. The $06D4 helper writes
       exactly 32 words of HL=$0000, i.e. 64 zero bytes to VRAM
       $0000-$003F. Stop at $0A77 before a much longer clear
       of $3800-$3EFF (which may cross a real frame IRQ).
       No CPU/VRAM edits, injected IRQ or host-controlled timing. */
    const uint64_t clear_irq_before=runtime.recognized_irqs;
    const uint64_t clear_vblank_before=runtime.clock.vblank_events;
    const uint64_t clear_vram_before=vdp->vram_writes;
    const uint64_t clear_cram_before=vdp->cram_writes;
    const uint64_t clear_registers_before=vdp->register_writes;
    const uint16_t clear_sp_before=cpu.sp;
    const uint8_t clear_slot2_before=bus->mapped_bank[2];
    unsigned clear_steps=0u;
    while(cpu.pc!=0x0A77u && clear_steps<800u &&
          runtime.recognized_irqs==clear_irq_before) {
        uint16_t prev_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M37 first source VRAM clear unsupported",&runtime);
            fprintf(stderr,"  priorPC=$%04X clearsteps=%u\n",prev_pc,clear_steps);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++clear_steps;
    }
    bool first_clear_ok=cpu.pc==0x0A77u &&
        clear_steps>200u && clear_steps<800u &&
        cpu.sp==clear_sp_before &&
        cpu.h==0u && cpu.l==0u &&
        cpu.d==0x40u && cpu.e==0u &&
        cpu.b==0u && cpu.c==0u &&
        bus->mapped_bank[2]==clear_slot2_before &&
        vdp->registers[8]==0u && vdp->registers[9]==0u &&
        vdp->register_writes==clear_registers_before+2u &&
        vdp->vram_writes==clear_vram_before+64u &&
        vdp->cram_writes==clear_cram_before &&
        vdp->address==0x40u && vdp->code==1u &&
        ys_sms_bus_read(bus,0xC018u)==0u &&
        ys_sms_bus_read(bus,0xC019u)==0u &&
        runtime.recognized_irqs==clear_irq_before &&
        runtime.clock.vblank_events==clear_vblank_before;
    for(unsigned i=0u;i<64u;++i)
        first_clear_ok=first_clear_ok && vdp->vram[i]==0u;
    if(!first_clear_ok) {
        int result=fail("M37 source scroll/64-byte VRAM initialization",&runtime);
        fprintf(stderr,"  steps=%u R8=%02X R9=%02X VRAMwrites=%llu->%llu"
                " VDPaddr=$%04X code=%u SP=$%04X\n",
                clear_steps,vdp->registers[8],vdp->registers[9],
                (unsigned long long)clear_vram_before,
                (unsigned long long)vdp->vram_writes,
                vdp->address,vdp->code,cpu.sp);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys first VRAM clear to $0A77:"
           " zero_bytes=64 R8=$%02X R9=$%02X"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu"
           " VRAMwrites=%llu\n",
           vdp->registers[8],vdp->registers[9],
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)vdp->vram_writes);
    puts("M37 small VRAM clear verified; continuing original $0A77 tail-JP.");

    /* M38: original bank 0 $0A77 sets DE=$7800 and BC=$0380,
       JP $06D4 (tail call) to write 896 zero words/1792 bytes.
       The helper RETs to the earlier CALL $0A5B caller $0C4D.
       The VBlank clock remains active: any genuine interrupt is
       accepted and serviced by the SAME game ISR, never injected. */
    const uint16_t ntable_sp=cpu.sp;
    const uint8_t ntable_mapper_control=bus->mapper_control;
    const uint8_t ntable_mapper_bank=bus->mapped_bank[2];
    const uint64_t ntable_prev_irq=runtime.recognized_irqs;
    const uint64_t ntable_prev_vblank=runtime.clock.vblank_events;
    const uint64_t ntable_prev_vram=vdp->vram_writes;
    const uint64_t ntable_prev_cram=vdp->cram_writes;
    const uint16_t ntable_saved_return=(uint16_t)(
        (uint16_t)ys_sms_bus_read(bus,ntable_sp) |
        ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(ntable_sp+1u))<<8));
    if(ntable_saved_return!=0x0C4Du) {
        int result=fail("M38 $0A5B tail-call return is not source $0C4D",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    unsigned long ntable_steps=0u;
    unsigned ntable_low=0u,ntable_high=0u;
    uint64_t ntable_last_irq=runtime.recognized_irqs;
    uint64_t ntable_irq_pc=0u;
    while(cpu.pc!=0x0C4Du && ntable_steps<30000ul) {
        uint16_t prior=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M38 source name-table VRAM clear stopped",&runtime);
            fprintf(stderr,"  priorPC=$%04X steps=%lu written=%u/%u\n",
                    prior,ntable_steps,ntable_low,ntable_high);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++ntable_steps;
        if(prior==0x06DBu && cpu.pc==0x06DDu) ++ntable_low;
        if(prior==0x06E0u && cpu.pc==0x06E2u) ++ntable_high;
        if(runtime.recognized_irqs!=ntable_last_irq) {
            if(runtime.recognized_irqs!=ntable_last_irq+1u ||
               cpu.pc!=0x0038u || (vdp->status&0x80u)==0u) {
                int result=fail("M38 source name-table interrupted by invalid IM1",&runtime);
                free(rom);free(bus);free(vdp);free(sound);return result;
            }
            ntable_irq_pc=(uint16_t)((uint16_t)ys_sms_bus_read(bus,cpu.sp) |
                ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(cpu.sp+1u))<<8));
            printf("PASS original Ys name-table clear natural IRQ:"
                   " savedPC=$%04X IRQ=%llu VBlank=%llu written=%u/%u\n",
                   (unsigned)ntable_irq_pc,
                   (unsigned long long)runtime.recognized_irqs,
                   (unsigned long long)runtime.clock.vblank_events,
                   ntable_low,ntable_high);
            ntable_last_irq=runtime.recognized_irqs;
        }
    }
    bool ntable_ok=cpu.pc==0x0C4Du && ntable_low==896u &&
        ntable_high==896u && ntable_steps>5000u &&
        cpu.sp==(uint16_t)(ntable_sp+2u) &&
        cpu.h==0u && cpu.l==0u &&
        cpu.d==0x78u && cpu.e==0u &&
        cpu.b==0u && cpu.c==0u &&
        bus->mapper_control==ntable_mapper_control &&
        bus->mapped_bank[2]==ntable_mapper_bank &&
        vdp->registers[8]==0u && vdp->registers[9]==0u &&
        vdp->vram_writes>=ntable_prev_vram+1792u &&
        vdp->cram_writes==ntable_prev_cram &&
        runtime.recognized_irqs>=ntable_prev_irq &&
        runtime.clock.vblank_events>=ntable_prev_vblank &&
        ys_sms_bus_read(bus,0xC018u)==0u &&
        ys_sms_bus_read(bus,0xC019u)==0u;
    if(!ntable_ok) {
        int result=fail("M38 1792-byte original name-table clear and $0C4D return",&runtime);
        fprintf(stderr,"  steps=%lu words=%u/%u SP=$%04X"
                " BC=%02X%02X DE=%02X%02X VRAM=%llu->%llu"
                " CRAM=%llu->%llu IRQ=%llu->%llu\n",
                ntable_steps,ntable_low,ntable_high,cpu.sp,
                cpu.b,cpu.c,cpu.d,cpu.e,
                (unsigned long long)ntable_prev_vram,
                (unsigned long long)vdp->vram_writes,
                (unsigned long long)ntable_prev_cram,
                (unsigned long long)vdp->cram_writes,
                (unsigned long long)ntable_prev_irq,
                (unsigned long long)runtime.recognized_irqs);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys 1792-byte name-table VRAM clear:"
           " PC=$0C4D words=%u steps=%llu T-states=%llu"
           " IRQ=%llu VBlank=%llu VRAMwrites=%llu\n",
           ntable_low,(unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)vdp->vram_writes);
    puts("M38 graphics table clear verified; enter bank-2 sound handoff.");

    /* M39: the original bank-0 $0C4D LD A,2 / $0C4F
       LD (MapperSlot2),A / $0C52 CALL $8803 must select
       physical bank 2 and push authentic $0C55 return PC.
       Stop BEFORE executing a bank-2 sound opcode. This verifies
       actual inter-bank call setup, not recompiled sound gameplay. */
    const uint16_t bank2_pre_sp=cpu.sp;
    const uint64_t bank2_pre_steps=cpu.steps;
    const uint64_t bank2_pre_tstates=cpu.total_tstates;
    const uint64_t bank2_pre_irq=runtime.recognized_irqs;
    const uint64_t bank2_pre_vblank=runtime.clock.vblank_events;
    const uint64_t bank2_pre_vram=vdp->vram_writes;
    const uint64_t bank2_pre_cram=vdp->cram_writes;
    const uint64_t bank2_pre_psg=sound->psg_write_count;
    unsigned bank2_steps=0;
    while(cpu.pc!=0x8803u && bank2_steps<4u) {
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M39 source bank-2 sound entry stopped",&runtime);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++bank2_steps;
    }
    const uint16_t bank2_return=(uint16_t)(
        (uint16_t)ys_sms_bus_read(bus,cpu.sp) |
        ((uint16_t)ys_sms_bus_read(bus,(uint16_t)(cpu.sp+1u))<<8));
    const uint8_t entry_opcode=ys_sms_bus_read(bus,0x8803u);
    if(cpu.pc!=0x8803u || bank2_steps!=3u ||
       cpu.sp!=(uint16_t)(bank2_pre_sp-2u) ||
       bank2_return!=0x0C55u ||
       cpu.a!=2u ||
       bus->mapped_bank[2]!=2u || bus->bank_select[2]!=2u ||
       cpu.steps!=bank2_pre_steps+3u ||
       cpu.total_tstates!=bank2_pre_tstates+37u ||
       entry_opcode!=rom[2u*YS_ROM_BANK_BYTES+0x0803u] ||
       runtime.recognized_irqs!=bank2_pre_irq ||
       runtime.clock.vblank_events!=bank2_pre_vblank ||
       vdp->vram_writes!=bank2_pre_vram ||
       vdp->cram_writes!=bank2_pre_cram ||
       sound->psg_write_count!=bank2_pre_psg) {
        int result=fail("M39 original source bank-2 $8803 call handoff",&runtime);
        fprintf(stderr,"  steps=%u bank2=%u return=$%04X opcode=$%02X\n",
                bank2_steps,bus->mapped_bank[2],bank2_return,entry_opcode);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS Ys source bank-2 sound handoff:"
           " PC=$8803 savedPC=$%04X bank2=%u opcode=$%02X"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu\n",
           bank2_return,bus->mapped_bank[2],entry_opcode,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events);
    puts("M39 bank-2 sound entry validated; M40 enters original sound init.");

    /* M40: source bank-2 $8803-$8877 is an actual sound-state reset
       and hardware initialization. Observe its 10 overlapping LDI
       clears and 8 zero-filled channel records, then its 11 PSG and
       6 YM2413 address/data writes. Continue naturally to $0C55.
       This verifies I/O LEDGER updates, not audible native audio. */
    const uint16_t sound_init_sp=cpu.sp;
    const uint64_t init_irq=runtime.recognized_irqs;
    const uint64_t init_vblank=runtime.clock.vblank_events;
    const uint64_t init_vram=vdp->vram_writes;
    const uint64_t init_cram=vdp->cram_writes;
    const uint64_t init_psg=sound->psg_write_count;
    const uint64_t init_fm_address=sound->fm_address_count;
    const uint64_t init_fm_data=sound->fm_data_count;
    const uint8_t init_bank=bus->mapped_bank[2];
    const uint16_t saved_hl=(uint16_t)(((uint16_t)cpu.h<<8)|cpu.l);
    const uint16_t saved_de=(uint16_t)(((uint16_t)cpu.d<<8)|cpu.e);
    const uint16_t saved_bc=(uint16_t)(((uint16_t)cpu.b<<8)|cpu.c);
    unsigned long init_steps=0u;
    unsigned ldi_steps=0u;
    unsigned psg_out_steps=0u;
    unsigned fm_addr_steps=0u;
    unsigned fm_data_steps=0u;
    bool visited_workspace=false;
    while(cpu.pc!=0x0C55u && init_steps<500ul &&
          runtime.recognized_irqs==init_irq) {
        const uint16_t prev_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M40 original bank-2 sound init unsupported",&runtime);
            fprintf(stderr,"  soundPC=$%04X initSteps=%lu PSG=%llu FM=%llu/%llu\n",
                    prev_pc,init_steps,
                    (unsigned long long)sound->psg_write_count,
                    (unsigned long long)sound->fm_address_count,
                    (unsigned long long)sound->fm_data_count);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++init_steps;
        if(prev_pc>=0x880Eu && prev_pc<=0x8820u &&
           !(prev_pc&1u) && cpu.pc==prev_pc+2u) ++ldi_steps;
        if(prev_pc==0x883Au && cpu.pc==0x883Cu) {
            visited_workspace=true;
            bool cleared=true;
            for(unsigned j=0;j<11u;++j)
                cleared=cleared &&
                    ys_sms_bus_read(bus,(uint16_t)(0xDE63u+j))==0u;
            if(!cleared || ldi_steps!=10u) {
                int result=fail("M40 bank-2 sound workspace clear",&runtime);
                free(rom);free(bus);free(vdp);free(sound);return result;
            }
        }
        if(prev_pc>=0x8849u && prev_pc<=0x885Du &&
           (prev_pc&1u) && cpu.pc==prev_pc+2u)
            ++psg_out_steps;
        if(prev_pc==0x8867u) ++fm_addr_steps;
        if(prev_pc==0x886Du) ++fm_data_steps;
    }
    bool init_ok=cpu.pc==0x0C55u && init_steps>100ul &&
        init_steps<500ul && visited_workspace &&
        ldi_steps==10u && psg_out_steps==11u &&
        fm_addr_steps==6u && fm_data_steps==6u &&
        cpu.sp==(uint16_t)(sound_init_sp+2u) &&
        (((uint16_t)cpu.h<<8)|cpu.l)==saved_hl &&
        (((uint16_t)cpu.d<<8)|cpu.e)==saved_de &&
        (((uint16_t)cpu.b<<8)|cpu.c)==saved_bc &&
        ys_sms_bus_read(bus,0xDE68u)==0xE4u &&
        bus->mapped_bank[2]==init_bank &&
        runtime.recognized_irqs==init_irq &&
        runtime.clock.vblank_events==init_vblank &&
        vdp->vram_writes==init_vram &&
        vdp->cram_writes==init_cram &&
        sound->psg_write_count==init_psg+11u &&
        sound->fm_address_count==init_fm_address+6u &&
        sound->fm_data_count==init_fm_data+6u;
    for(unsigned address=0x20u;address<=0x25u;++address)
        init_ok=init_ok && sound->fm_touched[address] &&
            sound->fm_registers[address]==0u;
    if(!init_ok) {
        int result=fail("M40 sound PSG/FM initialization and $0C55 return",&runtime);
        fprintf(stderr,"  initsteps=%lu LDI=%u PSG=%u FM=%u/%u"
                " SP=$%04X DE68=%02X"
                " PSGcount=%llu->%llu FMaddr=%llu->%llu FMdata=%llu->%llu\n",
                init_steps,ldi_steps,psg_out_steps,fm_addr_steps,fm_data_steps,
                cpu.sp,ys_sms_bus_read(bus,0xDE68u),
                (unsigned long long)init_psg,
                (unsigned long long)sound->psg_write_count,
                (unsigned long long)init_fm_address,
                (unsigned long long)sound->fm_address_count,
                (unsigned long long)init_fm_data,
                (unsigned long long)sound->fm_data_count);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS authentic Ys bank-2 sound init return: PC=$0C55"
           " LDI=%u PSG=%u FMaddr=%u FMdata=%u"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu\n",
           ldi_steps,psg_out_steps,fm_addr_steps,fm_data_steps,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events);
    puts("M40 sound setup validated; continue into bank-5 source RLE.");
    uint8_t expected_decompressed[0x1000];
    size_t expected_bytes=0u,compressed_bytes=0u;
    if(!reference_bank5_decode(rom,expected_decompressed,
                               sizeof(expected_decompressed),
                               &expected_bytes,&compressed_bytes)) {
        fputs("M41 bank-5 source RLE invalid or exceeds bounded WRAM workspace\n",
              stderr);
        free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
    }
    const uint16_t rle_entry_sp=cpu.sp;
    const uint64_t rle_start_irqs=runtime.recognized_irqs;
    const uint64_t rle_start_vblank=runtime.clock.vblank_events;
    unsigned long rle_steps=0ul;
    bool mapped_bank5=false;
    while(cpu.pc!=0x0C67u && rle_steps<180000ul) {
        uint16_t prev_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M41 source bank-5 RLE opcode unsupported",&runtime);
            fprintf(stderr,"  lastPC=$%04X RLE steps=%lu\n",prev_pc,rle_steps);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++rle_steps;
        if(prev_pc==0x0C5Bu && cpu.pc==0x0C5Eu)
            mapped_bank5=bus->mapped_bank[2]==5u;
    }
    const uint16_t final_hl=(uint16_t)(((uint16_t)cpu.h<<8)|cpu.l);
    const uint16_t final_de=(uint16_t)(((uint16_t)cpu.d<<8)|cpu.e);
    bool rle_ok=cpu.pc==0x0C67u && rle_steps<180000ul &&
        expected_bytes>0u && compressed_bytes>1u &&
        mapped_bank5 && bus->mapped_bank[2]==5u &&
        cpu.sp==rle_entry_sp &&
        ys_sms_bus_read(bus,0xC02Eu)==(uint8_t)rle_entry_sp &&
        ys_sms_bus_read(bus,0xC02Fu)==(uint8_t)(rle_entry_sp>>8) &&
        final_hl==(uint16_t)(0xB61Au+compressed_bytes) &&
        final_de==(uint16_t)(0xC600u+expected_bytes) &&
        runtime.recognized_irqs>=rle_start_irqs &&
        runtime.clock.vblank_events>=rle_start_vblank;
    for(size_t i=0;i<expected_bytes;++i)
        rle_ok=rle_ok && ys_sms_bus_read(bus,(uint16_t)(0xC600u+i))==
                expected_decompressed[i];
    if(!rle_ok) {
        int result=fail("M41 source bank-5 decompression mismatch",&runtime);
        fprintf(stderr,"  steps=%lu output=%zu compressed=%zu"
                " HL=$%04X DE=$%04X SP=$%04X bank2=%u\n",
                rle_steps,expected_bytes,compressed_bytes,
                final_hl,final_de,cpu.sp,bus->mapped_bank[2]);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys bank-5 compressed resource to $0C67:"
           " decoded_bytes=%zu source_bytes=%zu"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu\n",
           expected_bytes,compressed_bytes,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events);

    /* M42: original bank-5 resource is *staged* through the $0BEF
       two-row interleaved source stream. Compare the entire
       non-stack $D600-$DFBF destination and require 1536 writes.
       $DFC0-$DFFF is used by the live CPU/IRQ stack, so its
       mutations are expected and must not be mistaken for data.
       Preserve the real frame/mapper state; inject nothing. */
    /* $DFC0-$DFFF is the LIVE Z80 interrupt stack, not part of
       the resource staging buffer: snapshot-comparing it would
       misdiagnose legitimate IM1 pushes as corrupt source output. */
    enum { STAGING_CAPACITY=0x9C0u };
    uint8_t expected_staging[STAGING_CAPACITY];
    uint8_t source_staging[0x1000];
    for(unsigned i=0u;i<STAGING_CAPACITY;++i)
        expected_staging[i]=ys_sms_bus_read(bus,(uint16_t)(0xD600u+i));
    for(size_t i=0u;i<expected_bytes;++i)
        source_staging[i]=ys_sms_bus_read(bus,(uint16_t)(0xC600u+i));
    size_t staging_used=0u,staging_written=0u;
    if(!reference_staged_rows(source_staging,expected_bytes,
                              expected_staging,sizeof(expected_staging),
                              &staging_used,&staging_written)) {
        fputs("M42 decompressed resource has invalid two-row staging commands\n",
              stderr);
        free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
    }
    const uint64_t stage_irq=runtime.recognized_irqs;
    const uint64_t stage_vblank=runtime.clock.vblank_events;
    const uint64_t stage_vram=vdp->vram_writes;
    const uint64_t stage_psg=sound->psg_write_count;
    const uint16_t stage_sp=cpu.sp;
    const uint8_t stage_bank=bus->mapped_bank[2];
    unsigned long stage_steps=0ul;
    bool entered_decoder=false;
    while(cpu.pc!=0x0C72u && stage_steps<60000ul) {
        uint16_t prev_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M42 original resource staging unsupported",&runtime);
            fprintf(stderr,"  lastPC=$%04X stage_steps=%lu\n",
                    prev_pc,stage_steps);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++stage_steps;
        if(prev_pc==0x0C6Fu && cpu.pc==0x0BEFu)
            entered_decoder=true;
    }
    const uint16_t actual_stage_hl=(uint16_t)(((uint16_t)cpu.h<<8)|cpu.l);
    const uint16_t actual_stage_de=(uint16_t)(((uint16_t)cpu.d<<8)|cpu.e);
    bool stage_ok=cpu.pc==0x0C72u && entered_decoder &&
        stage_steps>15ul && stage_steps<60000ul &&
        staging_written==1536u && staging_used==expected_bytes &&
        actual_stage_hl==(uint16_t)(0xC600u+staging_used) &&
        actual_stage_de==0xD602u &&
        cpu.sp==stage_sp &&
        cpu.b==0u && cpu.c==2u &&
        bus->mapped_bank[2]==stage_bank &&
        /* This 1536-write source loop spans two *real* VBlanks.
           Do not mistake legitimate ISR/audio/VDP work for an
           emulator discontinuity or inject a fake frame to pass. */
        runtime.recognized_irqs>=stage_irq &&
        runtime.recognized_irqs<=stage_irq+4u &&
        runtime.clock.vblank_events>=stage_vblank &&
        runtime.clock.vblank_events<=stage_vblank+4u &&
        vdp->vram_writes>=stage_vram &&
        sound->psg_write_count>=stage_psg;
    size_t mismatches=0u;
    unsigned first_mismatch=0u;
    for(unsigned i=0u;i<STAGING_CAPACITY;++i) {
        if(ys_sms_bus_read(bus,(uint16_t)(0xD600u+i))!=
           expected_staging[i]) {
            if(mismatches==0u) first_mismatch=i;
            ++mismatches;
        }
    }
    stage_ok=stage_ok && mismatches==0u;
    if(!stage_ok) {
        int result=fail("M42 source decompressed tile/resource staging mismatch",
                        &runtime);
        fprintf(stderr,"  steps=%lu source_used=%zu writes=%zu"
                " HL=$%04X DE=$%04X SP=$%04X IRQ=%llu->%llu"
                " VBlank=%llu->%llu mismatches=%zu first=$%04X"
                " actual=%02X expected=%02X\n",
                stage_steps,staging_used,staging_written,
                actual_stage_hl,actual_stage_de,cpu.sp,
                (unsigned long long)stage_irq,
                (unsigned long long)runtime.recognized_irqs,
                (unsigned long long)stage_vblank,
                (unsigned long long)runtime.clock.vblank_events,
                mismatches,(unsigned)(0xD600u+first_mismatch),
                ys_sms_bus_read(bus,(uint16_t)(0xD600u+first_mismatch)),
                expected_staging[first_mismatch]);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS authentic Ys two-row staged resource to $0C72:"
           " source_used=%zu staged_writes=%zu"
           " steps=%llu T-states=%llu IRQ=%llu VBlank=%llu\n",
           staging_used,staging_written,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events);
    puts("M42 staged 1,536 bytes verified; continue original VDP upload.");

    /* M43: original $0C72-$0C7B selects VDP $3900, then CALL $06C1
       streams exactly BC=$0600 (1536) source bytes from $D600.
       Do not emulate a memcpy: execute 1536 real ED A3 OUTI
       instructions, through real $0028 VDP command, NOP/JR loops.
       Verify each output VRAM byte from a separate WRAM snapshot
       taken BEFORE execution. Preserve natural IRQ timing. */
    enum { TILE_UPLOAD_BYTES=0x600u, TILE_VRAM_START=0x3900u };
    uint8_t upload_reference[TILE_UPLOAD_BYTES];
    for(unsigned i=0;i<TILE_UPLOAD_BYTES;++i)
        upload_reference[i]=ys_sms_bus_read(bus,(uint16_t)(0xD600u+i));
    const uint16_t upload_entry_sp=cpu.sp;
    const uint64_t upload_entry_vblank=runtime.clock.vblank_events;
    const uint64_t upload_entry_irq=runtime.recognized_irqs;
    const uint64_t upload_entry_vram=vdp->vram_writes;
    const uint64_t upload_entry_cram=vdp->cram_writes;
    const uint64_t upload_entry_psg=sound->psg_write_count;
    unsigned upload_steps=0u, upload_outi=0u;
    bool upload_entered=false, upload_control_set=false;
    while(cpu.pc!=0x0C7Eu && upload_steps<15000u) {
        uint16_t prior_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M43 original source VRAM upload unsupported",&runtime);
            fprintf(stderr,"  lastPC=$%04X upload_steps=%u OUTI=%u\n",
                    prior_pc,upload_steps,upload_outi);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++upload_steps;
        if(prior_pc==0x0C7Bu && cpu.pc==0x06C1u) upload_entered=true;
        if(upload_entered && prior_pc==0x002Du &&
           vdp->address==TILE_VRAM_START && vdp->code==1u)
            upload_control_set=true;
        if(prior_pc==0x06CBu) ++upload_outi;
    }
    bool upload_ok=cpu.pc==0x0C7Eu && upload_entered &&
        upload_control_set && upload_outi==TILE_UPLOAD_BYTES &&
        upload_steps>4500u && upload_steps<15000u &&
        cpu.sp==upload_entry_sp &&
        cpu.h==0xDCu && cpu.l==0u &&
        cpu.d==0x79u && cpu.e==0u &&
        cpu.b==0u && cpu.c==0xBEu &&
        vdp->address==0x3F00u && vdp->code==1u &&
        vdp->vram_writes>=upload_entry_vram+TILE_UPLOAD_BYTES &&
        vdp->cram_writes==upload_entry_cram &&
        runtime.recognized_irqs>=upload_entry_irq &&
        runtime.recognized_irqs<=upload_entry_irq+3u &&
        runtime.clock.vblank_events>=upload_entry_vblank &&
        runtime.clock.vblank_events<=upload_entry_vblank+3u &&
        sound->psg_write_count>=upload_entry_psg;
    size_t upload_mismatch=0u;
    unsigned first_bad=0u;
    for(unsigned i=0;i<TILE_UPLOAD_BYTES;++i) {
        if(vdp->vram[TILE_VRAM_START+i]!=upload_reference[i]) {
            if(upload_mismatch==0u) first_bad=i;
            ++upload_mismatch;
        }
    }
    upload_ok=upload_ok && upload_mismatch==0u;
    if(!upload_ok) {
        int result=fail("M43 source resource to VRAM transfer mismatch",&runtime);
        fprintf(stderr,"  upload_steps=%u OUTI=%u SP=$%04X"
                " VRAMwrites=%llu->%llu VDPaddr=$%04X"
                " IRQ=%llu->%llu VBlank=%llu->%llu"
                " bad=%zu first=$%04X value=%02X expected=%02X\n",
                upload_steps,upload_outi,cpu.sp,
                (unsigned long long)upload_entry_vram,
                (unsigned long long)vdp->vram_writes,vdp->address,
                (unsigned long long)upload_entry_irq,
                (unsigned long long)runtime.recognized_irqs,
                (unsigned long long)upload_entry_vblank,
                (unsigned long long)runtime.clock.vblank_events,
                upload_mismatch,TILE_VRAM_START+first_bad,
                vdp->vram[TILE_VRAM_START+first_bad],
                upload_reference[first_bad]);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys staged tile bytes uploaded to VDP at $0C7E:"
           " bytes=%u OUTI=%u steps=%llu T-states=%llu"
           " IRQ=%llu VBlank=%llu VRAMwrites=%llu\n",
           TILE_UPLOAD_BYTES,upload_outi,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)vdp->vram_writes);
    /* M44: source $0C7E-$0C86 selects HL=$8000, DE=$4000,
       CALL $0695. The bank-0 decoder streams four interleaved
       compressed rows into VRAM using actual RST $28, OUT ($BE),
       mapper reads and Z80 loop timing. Compare against a separate
       bounded host decoder, never substitute the decoded bytes
       into the VDP or modify CPU/interrupt state. */
    uint8_t pattern_expected[YS_VRAM_BYTES];
    uint8_t pattern_touched[YS_VRAM_BYTES];
    size_t pattern_bytes=0u;
    uint16_t pattern_end_hl=0u;
    if(!reference_pattern_rows(bus,pattern_expected,pattern_touched,
                               &pattern_bytes,&pattern_end_hl)) {
        int result=fail("M44 source cartridge pattern reference invalid",&runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    const uint16_t pattern_sp=cpu.sp;
    const uint8_t pattern_bank=bus->mapped_bank[2];
    const uint64_t pattern_vblank=runtime.clock.vblank_events;
    const uint64_t pattern_irq=runtime.recognized_irqs;
    const uint64_t pattern_vram=vdp->vram_writes;
    const uint64_t pattern_cram=vdp->cram_writes;
    unsigned pattern_steps=0u;
    unsigned actual_out=0u;
    unsigned row_terminators=0u;
    while(cpu.pc!=0x0C87u && pattern_steps<200000u) {
        uint16_t prior_pc=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M44 original $0695 graphics transfer stopped",&runtime);
            fprintf(stderr,"  priorPC=$%04X helpersteps=%u outputs=%u\n",
                    prior_pc,pattern_steps,actual_out);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++pattern_steps;
        if(prior_pc==0x06A6u) ++actual_out;
        if(prior_pc==0x06BBu && cpu.pc==0x06BCu)
            ++row_terminators;
    }
    size_t bad_pixels=0u;
    unsigned first_bad=0u;
    for(unsigned i=0u;i<YS_VRAM_BYTES;++i)
        if(pattern_touched[i] && vdp->vram[i]!=pattern_expected[i]) {
            if(bad_pixels==0u) first_bad=i;
            ++bad_pixels;
        }
    bool pattern_ok=cpu.pc==0x0C87u &&
        pattern_bytes>0u && actual_out==pattern_bytes &&
        row_terminators==4u &&
        pattern_steps>100u && pattern_steps<200000u &&
        cpu.sp==pattern_sp && cpu.h==(uint8_t)(pattern_end_hl>>8) &&
        cpu.l==(uint8_t)pattern_end_hl &&
        cpu.d==0x40u && cpu.e==4u && cpu.b==0u && cpu.c==4u &&
        bus->mapped_bank[2]==pattern_bank &&
        vdp->vram_writes>=pattern_vram+pattern_bytes &&
        vdp->cram_writes==pattern_cram &&
        runtime.recognized_irqs>=pattern_irq &&
        runtime.clock.vblank_events>=pattern_vblank &&
        bad_pixels==0u;
    if(!pattern_ok) {
        int result=fail("M44 source four-row graphics mismatch",&runtime);
        fprintf(stderr,"  rows=%u writes=%u expected=%zu bad=%zu"
                " first=$%04X actual=%02X expected=%02X"
                " HL=$%02X%02X expectedHL=$%04X DE=$%02X%02X"
                " steps=%u\n",
                row_terminators,actual_out,pattern_bytes,bad_pixels,
                first_bad,vdp->vram[first_bad],pattern_expected[first_bad],
                cpu.h,cpu.l,pattern_end_hl,cpu.d,cpu.e,pattern_steps);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys 4-row pattern decompression to $0C87:"
           " bytes=%zu OUT=%u sourceHL=$%04X"
           " Z80steps=%llu T-states=%llu IRQ=%llu VBlank=%llu"
           " VRAMwrites=%llu\n",
           pattern_bytes,actual_out,pattern_end_hl,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events,
           (unsigned long long)vdp->vram_writes);
    puts("Stop before source $0C87 resource staging; not playable.");










    if (argc==4) {
        uint8_t *rgb=malloc(YS_SMS_RGB_BYTES);
        if (!rgb) {
            fputs("cannot allocate RGB frame\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        bool ok=ys_sms_video_render(vdp,rgb,YS_SMS_RGB_BYTES,NULL);
        FILE *output=ok?fopen(argv[3],"wb"):NULL;
        if(!output) ok=false;
        if(ok && !ys_sms_video_write_ppm(output,rgb,YS_SMS_RGB_BYTES))
            ok=false;
        if(output && fclose(output)!=0) ok=false;
        free(rgb);
        if(!ok) {
            fputs("cannot render/write real Ys first-frame VDP snapshot\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        printf("PASS saved original Ys ROM VDP state at PC=$0C87: %s"
               " (256x192 PPM; may be blank during initialization)\n",argv[3]);
    }
    free(rom);free(bus);free(vdp);free(sound);
    return EXIT_SUCCESS;
}
