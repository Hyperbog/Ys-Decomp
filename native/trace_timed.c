/* M30 original-ROM reset through TWO clock-generated VBlank IM1 events,
   including legitimate immediate re-entry and a stable return to $0764.
   This is a bounded diagnostic, never interactive gameplay. No injected IRQ. */
#include "sms_runtime.h"
#include "sms_video.h"
#include "pc_vdp_checkpoint.h"
#include "pc_source_watch.h"
#include "pc_sprite_watch.h"
#include "pc_sprite_upload_watch.h"
#include "pc_sat_provenance.h"
#include "pc_sat_strobes.h"
#include "pc40_route.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* PC-37 fingerprints read-only VDP state and its rendered RGB snapshot. */
static uint32_t pc37_crc32(const uint8_t *p,size_t count) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<count;++i) {
        crc^=p[i];
        for(unsigned bit=0;bit<8u;++bit)
            crc=(crc>>1u)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}


/* PC-26 source-only fixed-bank input/selector observation.
   This is a passive audit of known Phase2 sampler opcodes, never
   an input injection, menu-state inference or game progression. */
enum { PC26_SITES=6 };
static const uint16_t pc26_sites[PC26_SITES]={
    0x0126u,0x012Du,0x0773u,0x077Du,0x0780u,0x0138u
};
typedef struct {
    uint64_t count, first_step, last_step;
    uint8_t first_selector, last_selector, last_pressed, last_edges;
} Pc26Site;
typedef struct {
    Pc26Site sites[PC26_SITES];
    uint64_t samples, selector_changes, nonzero_pressed, nonzero_edges;
    uint8_t initial_selector, initial_pressed, initial_edges, last_selector;
} Pc26Audit;
static bool pc26_sample(Pc26Audit *out,const YsSmsRuntime *rt) {
    if(!out || !rt || !rt->cpu || !rt->cpu->bus ||
       !rt->cpu->input || !rt->cpu->vdp ||
       out->samples==UINT64_MAX) return false;
    const YsZ80 *cpu=rt->cpu;
    uint8_t selector=ys_sms_bus_read(cpu->bus,0xC01Fu);
    uint8_t pressed=ys_sms_bus_read(cpu->bus,0xC01Bu);
    uint8_t edges=ys_sms_bus_read(cpu->bus,0xC01Cu);
    if(out->samples==0u) {
        out->initial_selector=selector;
        out->initial_pressed=pressed;
        out->initial_edges=edges;
    } else if(selector!=out->last_selector) {
        ++out->selector_changes;
    }
    out->last_selector=selector;
    if(pressed!=0u) ++out->nonzero_pressed;
    if(edges!=0u) ++out->nonzero_edges;
    ++out->samples;
    for(unsigned i=0;i<PC26_SITES;++i) {
        if(cpu->pc!=pc26_sites[i]) continue;
        Pc26Site *p=&out->sites[i];
        if(p->count==0u) {
            p->first_step=cpu->steps;
            p->first_selector=selector;
        }
        if(p->count!=UINT64_MAX) ++p->count;
        p->last_step=cpu->steps;
        p->last_selector=selector;
        p->last_pressed=pressed;
        p->last_edges=edges;
        break;
    }
    return true;
}
static bool pc26_write(FILE *file,const Pc26Audit *audit,
                       const YsSmsRuntime *rt,
                       const char *reason,unsigned long executed) {
    if(!file || !audit || !audit->samples || !rt || !rt->cpu ||
       !rt->cpu->bus || !rt->cpu->input || !rt->cpu->vdp ||
       !reason) return false;
    const YsZ80 *cpu=rt->cpu;
    const YsSmsInput *input=cpu->input;
    if(fprintf(file,
       "{\n  \"schema\":\"ys-pc26-original-input-audit-v1\",\n"
       "  \"start_pc\":\"0C92\",\"stop_reason\":\"%s\",\n"
       "  \"continued_steps\":%lu,\"samples\":%llu,\n"
       "  \"stop_pc\":\"%04X\",\"stop_slot1\":%u,\"stop_slot2\":%u,\n"
       "  \"stop_irq\":%llu,\"stop_vblank\":%llu,\n"
       "  \"input_dc\":%u,\"input_dd\":%u,"
       "\"reads_dc\":%llu,\"reads_dd\":%llu,\n"
       "  \"initial_selector\":%u,\"last_selector\":%u,"
       "\"initial_pressed\":%u,\"initial_edges\":%u,\n"
       "  \"last_pressed\":%u,\"last_edges\":%u,\n"
       "  \"selector_changes\":%llu,\"nonzero_pressed_samples\":%llu,"
       "\"nonzero_edge_samples\":%llu,\n"
       "  \"vram_writes\":%llu,\"cram_writes\":%llu,"
       "\"display_reg1\":%u,\n  \"sites\":[\n",
       reason,executed,(unsigned long long)audit->samples,cpu->pc,
       (unsigned)cpu->bus->mapped_bank[1],
       (unsigned)cpu->bus->mapped_bank[2],
       (unsigned long long)rt->recognized_irqs,
       (unsigned long long)rt->clock.vblank_events,
       (unsigned)input->dc,(unsigned)input->dd,
       (unsigned long long)input->reads_dc,
       (unsigned long long)input->reads_dd,
       (unsigned)audit->initial_selector,
       (unsigned)audit->last_selector,
       (unsigned)audit->initial_pressed,
       (unsigned)audit->initial_edges,
       (unsigned)ys_sms_bus_read(cpu->bus,0xC01Bu),
       (unsigned)ys_sms_bus_read(cpu->bus,0xC01Cu),
       (unsigned long long)audit->selector_changes,
       (unsigned long long)audit->nonzero_pressed,
       (unsigned long long)audit->nonzero_edges,
       (unsigned long long)cpu->vdp->vram_writes,
       (unsigned long long)cpu->vdp->cram_writes,
       (unsigned)cpu->vdp->registers[1])<0) return false;
    for(unsigned i=0;i<PC26_SITES;++i) {
        const Pc26Site *p=&audit->sites[i];
        if(fprintf(file,
          "    {\"pc\":\"%04X\",\"count\":%llu,"
          "\"first_step\":%llu,\"last_step\":%llu,"
          "\"first_selector\":%u,\"last_selector\":%u,"
          "\"last_pressed\":%u,\"last_edges\":%u}%s\n",
          pc26_sites[i],(unsigned long long)p->count,
          (unsigned long long)p->first_step,
          (unsigned long long)p->last_step,
          (unsigned)p->first_selector,(unsigned)p->last_selector,
          (unsigned)p->last_pressed,(unsigned)p->last_edges,
          i+1u<PC26_SITES?",":"")<0) return false;
    }
    return fputs("  ]\n}\n",file)>=0 && ferror(file)==0;
}

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

/* M45 host-only reference: original $0BEF four-column RLE.
   Keep source and output disjoint from live Z80 bus. A write mask
   distinguishes untouched WRAM (including stack/IRQ effects) from
   bytes which must match the decoded stream exactly. */
static bool reference_staged_columns(const uint8_t *source,size_t size,
                                     uint8_t *expected,uint8_t *touched,
                                     size_t capacity,unsigned columns,
                                     size_t *consumed,size_t *written) {
    if(!source || !expected || !touched || !consumed || !written ||
       columns==0u || columns>8u || capacity<columns) return false;
    size_t at=0u,count=0u;
    for(unsigned column=0u;column<columns;++column) {
        size_t target=column;
        bool terminated=false;
        for(unsigned commands=0u;commands<4096u && at<size;++commands) {
            uint8_t command=source[at++];
            if(command==0u) {terminated=true;break;}
            unsigned n=command&0x7Fu;
            if(n==0u) n=256u; /* B=$00 loops 256 times on DJNZ. */
            bool literal=(command&0x80u)!=0u;
            if(at+(literal?n:1u)>size) return false;
            for(unsigned i=0u;i<n;++i) {
                if(target>=capacity) return false;
                expected[target]=source[at+(literal?i:0u)];
                touched[target]=1u;
                ++count;
                target+=columns;
            }
            at+=literal?n:1u;
        }
        if(!terminated) return false;
    }
    *consumed=at;*written=count;
    return count>0u;
}

int main(int argc,char **argv) {
    if (!(argc==2 || (argc==4 &&
          (strcmp(argv[2],"--frame")==0 ||
           strcmp(argv[2],"--vdp-at-m44")==0 ||
           strcmp(argv[2],"--pc12-watch")==0 ||
           strcmp(argv[2],"--pc15-sprite-watch")==0 ||
           strcmp(argv[2],"--pc25-collision-watch")==0 ||
           strcmp(argv[2],"--pc27-button-probe")==0 ||
           strcmp(argv[2],"--pc33-postrelease-watch")==0 ||
           strcmp(argv[2],"--pc34-extended-postrelease")==0)) ||
          (argc==5 &&
           (strcmp(argv[2],"--pc25-collision-watch")==0 ||
            strcmp(argv[2],"--pc34-extended-postrelease")==0 ||
            strcmp(argv[2],"--pc40-source-route")==0)) ||
          ((argc==6 || argc==8 || argc==9 || argc==10) &&
           strcmp(argv[2],"--pc34-extended-postrelease")==0))) {
        fputs("usage: ys-native-timed-rom source-Ys.sms [--frame snapshot.ppm | --vdp-at-m44 source.vdp | --pc12-watch watch.json | --pc15-sprite-watch sprite-watch.json]\n"
              "PC12/15 use 150k idle input; PC25 adds a 300k idle-only audit; PC27 is the source-armed button1 probe; PC33 runs 150k post-M45, PC34 separately extends to 300k after genuine release. Neither proves gameplay.\n",
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
    /* PC-39 records ALL actual original Z80 SAT WRAM stores from reset
       through M45, then through the existing PC-34 300k-step input run.
       Opt-in only, no change to bus writes or CPU execution. */
    const bool pc39_mode=(argc==10 &&
        strcmp(argv[2],"--pc34-extended-postrelease")==0);
    YsPcSatStrobeAudit pc39={0};
    pc39.cpu=&cpu;
    if(pc39_mode &&
       !ys_sms_bus_set_wram_hook(bus,ys_pc_sat_strobes_hook,&pc39)) {
        fputs("PC-39 failed to attach passive WRAM strobe observer\n",stderr);
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
        /* PC-42: an acknowledged IM1 clears BOTH IFF1 and IFF2.
           The older test erroneously preserved IFF2 across IRQ 2.
           The source $01AA EI reinstates both before IRQ 2;
           the IRQ then clears both again. */
        !cpu.iff2 && (vdp->status&0x80u)!=0u &&
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
    while(cpu.pc!=0x0C87u && pattern_steps<500000u) {
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
    unsigned pattern_first_bad=0u;
    for(unsigned i=0u;i<YS_VRAM_BYTES;++i)
        if(pattern_touched[i] && vdp->vram[i]!=pattern_expected[i]) {
            if(bad_pixels==0u) pattern_first_bad=i;
            ++bad_pixels;
        }
    bool pattern_ok=cpu.pc==0x0C87u &&
        pattern_bytes>0u && actual_out==pattern_bytes &&
        row_terminators==4u &&
        pattern_steps>100u && pattern_steps<500000u &&
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
                pattern_first_bad,vdp->vram[pattern_first_bad],pattern_expected[pattern_first_bad],
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

    /* PC-8: snapshot actual *simultaneously resident* VDP state
       immediately upon real-source return to PC=$0C87 after M44.
       No Z80/VDP RAM/register changes or runtime shortcuts. */
    if(argc==4 && strcmp(argv[2],"--vdp-at-m44")==0) {
        FILE *snapshot=fopen(argv[3],"wb");
        bool saved=snapshot &&
            ys_pc_vdp_checkpoint_save(snapshot,vdp,cpu.pc);
        if(snapshot && fclose(snapshot)!=0) saved=false;
        if(!saved) {
            fputs("PC-8 cannot write M44 VDP state capture\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);
            return EXIT_FAILURE;
        }
        printf("PASS PC-8 original simultaneous VDP capture at PC=$%04X:"
               " 16384 VRAM, 32 CRAM, 16 registers, IRQ=%llu VBlank=%llu\n",
               cpu.pc,
               (unsigned long long)runtime.recognized_irqs,
               (unsigned long long)runtime.clock.vblank_events);
    }

    /* M45: original bank-0 $0C87-$0C91 selects HL=$A4D1,
       DE=$C600, C=4, and calls $0BEF. The real source routine
       transfers FOUR interleaved compressed resource columns
       into WRAM. Compare against an independent bounded host
       decoder and source bank-2 mapper reads; never inject RAM,
       CPU state, VBlank or synthesized resource contents. */
    enum { FOUR_COLUMN_CAP=0x1600u, FOUR_SOURCE_AT=0xA4D1u };
    uint8_t four_source[0xC000u-FOUR_SOURCE_AT];
    uint8_t four_expected[FOUR_COLUMN_CAP];
    uint8_t four_written[FOUR_COLUMN_CAP];
    size_t four_consumed=0u, four_count=0u;
    for(unsigned i=0u;i<sizeof(four_source);++i)
        four_source[i]=ys_sms_bus_read(bus,(uint16_t)(FOUR_SOURCE_AT+i));
    for(unsigned i=0u;i<FOUR_COLUMN_CAP;++i)
        four_expected[i]=ys_sms_bus_read(bus,(uint16_t)(0xC600u+i));
    memset(four_written,0,sizeof(four_written));
    if(!reference_staged_columns(four_source,sizeof(four_source),
                                 four_expected,four_written,
                                 FOUR_COLUMN_CAP,4u,
                                 &four_consumed,&four_count)) {
        int result=fail("M45 invalid source four-column compressed stream",
                        &runtime);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    const uint16_t four_stack_before=cpu.sp;
    const uint8_t four_bank_before=bus->mapped_bank[2];
    const uint64_t four_irq_before=runtime.recognized_irqs;
    const uint64_t four_blank_before=runtime.clock.vblank_events;
    const uint64_t four_vram_before=vdp->vram_writes;
    const uint64_t four_psg_before=sound->psg_write_count;
    unsigned long four_steps=0ul;
    bool four_entered=false;
    while(cpu.pc!=0x0C92u && four_steps<400000ul) {
        const uint16_t previous=cpu.pc;
        Z80Status status=ys_sms_runtime_step_auto(&runtime);
        if(status!=Z80_RUNNING) {
            int result=fail("M45 original four-column resource decode stopped",
                            &runtime);
            fprintf(stderr,"  priorPC=$%04X foursteps=%lu\n",
                    previous,four_steps);
            free(rom);free(bus);free(vdp);free(sound);return result;
        }
        ++four_steps;
        if(previous==0x0C8Fu && cpu.pc==0x0BEFu) four_entered=true;
    }
    size_t four_bad=0u, four_first_bad=0u, four_touched=0u;
    for(unsigned i=0u;i<FOUR_COLUMN_CAP;++i)
        if(four_written[i]) {
            ++four_touched;
            if(ys_sms_bus_read(bus,(uint16_t)(0xC600u+i))!=four_expected[i]) {
                if(four_bad==0u) four_first_bad=i;
                ++four_bad;
            }
        }
    bool four_ok=cpu.pc==0x0C92u && four_entered &&
        four_steps>30ul && four_steps<400000ul &&
        four_consumed==4425u && four_count==5344u &&
        four_count==four_touched && four_bad==0u &&
        cpu.sp==four_stack_before &&
        (((uint16_t)cpu.h<<8)|cpu.l)==(uint16_t)(FOUR_SOURCE_AT+four_consumed) &&
        cpu.d==0xC6u && cpu.e==4u &&
        cpu.b==0u && cpu.c==4u &&
        bus->mapped_bank[2]==four_bank_before &&
        runtime.recognized_irqs>=four_irq_before &&
        runtime.clock.vblank_events>=four_blank_before &&
        vdp->vram_writes>=four_vram_before &&
        sound->psg_write_count>=four_psg_before;
    if(!four_ok) {
        int result=fail("M45 source four-column WRAM resource mismatch",
                        &runtime);
        fprintf(stderr,"  columns=4 decoded=%zu consumed=%zu"
                " touched=%zu bad=%zu firstWRAM=$%04X"
                " HL=$%02X%02X DE=$%02X%02X steps=%lu"
                " IRQ=%llu->%llu\n",
                four_count,four_consumed,four_touched,four_bad,
                0xC600u+(unsigned)four_first_bad,
                cpu.h,cpu.l,cpu.d,cpu.e,four_steps,
                (unsigned long long)four_irq_before,
                (unsigned long long)runtime.recognized_irqs);
        free(rom);free(bus);free(vdp);free(sound);return result;
    }
    printf("PASS original Ys 4-column resource staging to $0C92:"
           " bytes=%zu source_used=%zu steps=%llu"
           " T-states=%llu IRQ=%llu VBlank=%llu\n",
           four_count,four_consumed,
           (unsigned long long)cpu.steps,
           (unsigned long long)cpu.total_tstates,
           (unsigned long long)runtime.recognized_irqs,
           (unsigned long long)runtime.clock.vblank_events);
    if(argc==4 && strcmp(argv[2],"--pc12-watch")==0) {
        /* PC-12: only CONTINUE the already verified original M45 CPU,
           mapper, WRAM, VDP, clock and IRQ state. Never patch PC,
           input, memory, mapper state or VBlank. Source execution
           may STOP on an unsupported instruction before any scene. */
        enum { PC12_STEP_LIMIT=150000u,PC12_EXTRA_VBLANKS=90u };
        const uint64_t start_blank=runtime.clock.vblank_events;
        YsPcSourceWatch watch={0};
        const char *why="budget";
        unsigned long seen_steps=0ul;
        for(;seen_steps<PC12_STEP_LIMIT;++seen_steps) {
            if(!ys_pc_source_watch_sample(&watch,&runtime)) {
                fputs("PC-12 invalid read-only original observer state\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            if(watch.observed_collision_calls!=0u) {
                why="observed";break;
            }
            if(runtime.clock.vblank_events-start_blank>=PC12_EXTRA_VBLANKS) {
                why="vblank_limit";break;
            }
            Z80Status state=ys_sms_runtime_step_auto(&runtime);
            if(state!=Z80_RUNNING && state!=Z80_HALTED) {
                why="unsupported";break;
            }
        }
        FILE *file=fopen(argv[3],"wb");
        bool ok=file && ys_pc_source_watch_write(file,&watch,&runtime,
                                                  why,seen_steps);
        if(file && fclose(file)!=0) ok=false;
        if(!ok) {
            fputs("PC-12 cannot write observation result\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        printf("PC-12 original source continuation from verified M45:"
               " reason=%s continuation_steps=%lu PC=$%04X"
               " slot1=%u slot2=%u source_collision_calls=%u"
               " IRQ=%llu VBlank=%llu\n",
               why,seen_steps,cpu.pc,(unsigned)bus->mapped_bank[1],
               (unsigned)bus->mapped_bank[2],watch.observed_collision_calls,
               (unsigned long long)runtime.recognized_irqs,
               (unsigned long long)runtime.clock.vblank_events);
        if(watch.observed_collision_calls==0u)
            puts("BLOCKED PC-12: no actual original bank1 collision call"
                 " witnessed in bounded continuation;"
                 " no gameplay/map proof");
        else
            puts("OBSERVED PC-12: original mapped bank1 collision PC"
                 " reached; inspect JSON for mapper/WRAM/IX context;"
                 " still not proof of a playable scene");
    } else if(argc==4 && strcmp(argv[2],"--pc15-sprite-watch")==0) {
        /* PC-15: original CPU CONTINUATION from identical verified
           M45 state. No mapper, controller, VDP or RAM injections.
           First source bank6 $9932 entry is qualified by physical
           bank6 present in slot2, not its CPU address alone. */
        enum { PC15_STEPS=150000u,PC15_EXTRA_VBLANKS=90u };
        YsPcSpriteWatch watch={0};
        const uint64_t start_blank=runtime.clock.vblank_events;
        const char *why="budget";
        unsigned long steps=0ul;
        for(;steps<PC15_STEPS;++steps) {
            if(!ys_pc_sprite_watch_sample(&watch,&runtime)) {
                fputs("PC-15 invalid original sprite source sampler\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            if(watch.seen[3]) {why="observed";break;}
            if(runtime.clock.vblank_events-start_blank>=PC15_EXTRA_VBLANKS) {
                why="vblank_limit";break;
            }
            Z80Status result=ys_sms_runtime_step_auto(&runtime);
            if(result!=Z80_RUNNING && result!=Z80_HALTED) {
                why="unsupported";break;
            }
        }
        FILE *file=fopen(argv[3],"wb");
        bool ok=file &&
            ys_pc_sprite_watch_write(file,&watch,&runtime,why,steps);
        if(file && fclose(file)!=0) ok=false;
        if(!ok) {
            fputs("PC-15 cannot write source sprite watch report\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        printf("PC-15 source sprite watch: reason=%s steps=%lu"
               " PC=$%04X slot2=%u $9932_hits=%u"
               " IRQ=%llu VBlank=%llu\n",
               why,steps,cpu.pc,(unsigned)bus->mapped_bank[2],
               watch.counts[3],
               (unsigned long long)runtime.recognized_irqs,
               (unsigned long long)runtime.clock.vblank_events);
        if(watch.seen[3])
            puts("OBSERVED PC-15: actual mapped bank6 sprite producer"
                 " entered; JSON records raw selector/origins;"
                 " sprite and scene identities UNVERIFIED");
        else
            puts("BLOCKED PC-15: no original mapped bank6 sprite"
                 " producer observed; no original player/scene proof");
    } else if((argc==4 || argc==5) &&
              strcmp(argv[2],"--pc25-collision-watch")==0) {
        /* PC-25 is a SEPARATE opt-in research bound, not a change to
           PC-12/15 regression observers, original ROM or test oracles.
           Keep source CPU/IRQ/controller/RAM/mapper untouched. */
        enum { PC25_STEPS=300000u,PC25_EXTRA_VBLANKS=120u };
        const uint64_t start_blank=runtime.clock.vblank_events;
        YsPcSourceWatch watch={0};
        Pc26Audit audit={0};
        const bool audit_enabled=(argc==5);
        const char *why="budget";
        unsigned long steps=0ul;
        for(;steps<PC25_STEPS;++steps) {
            if(audit_enabled && !pc26_sample(&audit,&runtime)) {
                fputs("PC-26 invalid read-only input observation\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            if(!ys_pc_source_watch_sample(&watch,&runtime)) {
                fputs("PC-25 invalid read-only collision observer state\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            if(watch.observed_collision_calls!=0u) {
                why="observed";break; /* BEFORE executing source call. */
            }
            if(runtime.clock.vblank_events-start_blank>=PC25_EXTRA_VBLANKS) {
                why="vblank_limit";break;
            }
            Z80Status state=ys_sms_runtime_step_auto(&runtime);
            if(state!=Z80_RUNNING && state!=Z80_HALTED) {
                why="unsupported";break;
            }
        }
        FILE *file=fopen(argv[3],"wb");
        bool ok=file && ys_pc_source_watch_write(file,&watch,&runtime,
                                                  why,steps);
        if(file && fclose(file)!=0) ok=false;
        if(!ok) {
            fputs("PC-25 cannot write extended collision observation\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        if(audit_enabled) {
            FILE *audit_file=fopen(argv[4],"wb");
            bool audit_ok=audit_file &&
                pc26_write(audit_file,&audit,&runtime,why,steps);
            if(audit_file && fclose(audit_file)!=0) audit_ok=false;
            if(!audit_ok) {
                fputs("PC-26 cannot write read-only input report\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            printf("PC-26 original input sampler audit:"
                   " sites_0773=%llu reads_DC=%llu reads_DD=%llu"
                   " selector_changes=%llu pressed_samples=%llu"
                   " C01F=$%02X C01B=$%02X C01C=$%02X\n",
                   (unsigned long long)audit.sites[2].count,
                   (unsigned long long)input.reads_dc,
                   (unsigned long long)input.reads_dd,
                   (unsigned long long)audit.selector_changes,
                   (unsigned long long)audit.nonzero_pressed,
                   (unsigned)ys_sms_bus_read(bus,0xC01Fu),
                   (unsigned)ys_sms_bus_read(bus,0xC01Bu),
                   (unsigned)ys_sms_bus_read(bus,0xC01Cu));
        }
        printf("PC-25 extended original source collision research:"
               " reason=%s continuation_steps=%lu PC=$%04X"
               " slot1=%u slot2=%u original_calls=%u"
               " IRQ=%llu VBlank=%llu\n",
               why,steps,cpu.pc,(unsigned)bus->mapped_bank[1],
               (unsigned)bus->mapped_bank[2],watch.observed_collision_calls,
               (unsigned long long)runtime.recognized_irqs,
               (unsigned long long)runtime.clock.vblank_events);
        if(watch.observed_collision_calls>0u)
            puts("OBSERVED PC-25: mapper-qualified source collision call"
                 " before execution; source player and scene still unverified");
        else
            puts("BLOCKED PC-25: no source collision call within this"
                 " larger original unpressed-input research horizon");

    } else if((argc==4 &&
              (strcmp(argv[2],"--pc27-button-probe")==0 ||
               strcmp(argv[2],"--pc33-postrelease-watch")==0 ||
               strcmp(argv[2],"--pc34-extended-postrelease")==0)) ||
              ((argc==5 || argc==6 || argc==8 || argc==9 || argc==10) &&
               strcmp(argv[2],"--pc34-extended-postrelease")==0) ||
              (argc==5 && strcmp(argv[2],"--pc40-source-route")==0)) {
        /* Independent opt-in source-backed input experiment, not a
           hardware/emulator-match claim. Idle until original CPU
           reaches PC $0CD1 (observed Phase5 C01C edge test) with C01F==$01.
           Deliver active-low DC bit4 at first subsequent ORIGINAL
           IN A,($DC) at $0773. Release at NEXT $0773 sampling.
           Never edit Z80 PC, WRAM, mapper, timing, or IRQ state. */
        /* Separate 150k (PC27/33) and 300k (PC34) source budgets. */
        const uint64_t start_blank=runtime.clock.vblank_events;
        YsPcSourceWatch collision={0};
        YsPcSpriteWatch sprite={0};
        YsPcSpriteUploadWatch upload={0};
        YsPcSatProvenance provenance={0};
        YsPc40Route route={0};
        const bool route_long=strcmp(argv[2],"--pc40-source-route")==0;
        const bool extended=
            strcmp(argv[2],"--pc34-extended-postrelease")==0;
        const bool video_audit=extended && argc>=5;
        const bool upload_audit=extended && argc>=6;
        const bool frame_audit=extended && argc>=8;
        const bool provenance_audit=extended && argc>=9;
        if(pc39_mode && !ys_pc_sat_strobes_set_phase(&pc39,1u)) {
            fputs("PC-39 cannot enter post-M45 observation phase\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        /* Captured after the SECOND natural $053F return for each upload;
           there are no writes back into the running source machine. */
        YsSmsVdp pc37_vdp={0};
        unsigned pc37_captures=0u,pc37_enabled=0u;
        bool pc37_have=false,pc37_selected_enabled=false;
        unsigned long pc37_step=0ul;
        uint64_t pc37_irq=0u,pc37_vblank=0u;
        uint8_t pc37_slot2=0u,pc37_selector=0u;
        /* PC-35 independently samples the exact same source CPU run:
           controller state and PC/WRAM/VDP/mapper are never modified. */
        uint64_t display_enabled_samples=0u,display_transitions=0u;
        uint64_t selector_transitions=0u,slot2_transitions=0u;
        uint64_t first_display_step=0u,first_selector2_step=0u;
        uint8_t last_display=(uint8_t)
            ((vdp->registers[1] & 0x40u)!=0u);
        uint8_t last_mode=ys_sms_bus_read(bus,0xC01Fu);
        uint8_t last_slot2=bus->mapped_bank[2];
        const uint64_t initial_vram=vdp->vram_writes;
        const uint64_t initial_cram=vdp->cram_writes;
        const bool postrelease=extended || route_long ||
            strcmp(argv[2],"--pc33-postrelease-watch")==0;
        const unsigned step_budget=route_long?600000u:
                                   extended?300000u:150000u;
        const uint64_t blank_budget=route_long?240u:
                                    extended?120u:90u;
        bool release_sampled=false;
        const uint8_t start_selector=ys_sms_bus_read(bus,0xC01Fu);
        const char *why="budget";
        unsigned long steps=0ul;
        bool armed=false,pressed=false,released=false;
        bool saw_mode_write=false,saw_mode2=false;
        unsigned arm_hits=0u,hits_edge=0u,hits_mode_write=0u;
        uint8_t last_edge=0u;
        uint64_t press_step=0u,release_step=0u,mode2_step=0u;
        unsigned edge_10_hits=0u;
        for(;steps<step_budget;++steps) {
            /* PC-41 stopped on ED 5F LD A,R. Verify its complete
               read-only physical source history before PC-42 runs it.
               Print REAL R/IFF2, never synthesize refresh register. */
            if(route_long && steps==531478ul) {
                if(!ys_pc42_historical_checkpoint(&route,&runtime,steps,
                                                    sprite.counts,
                                                    collision.observed_collision_calls)) {
                    fputs("PC-42 original 531478-step checkpoint drift\n",stderr);
                    free(rom);free(bus);free(vdp);free(sound);
                    return EXIT_FAILURE;
                }
                printf("PC-42 PASS original PC-41 pre-LD-A-R"
                       " step=531478 R=%02X IFF2=%u"
                       " IRQ=%llu VBlank=%llu PC=%04X\n",
                       cpu.r,(unsigned)cpu.iff2,
                       (unsigned long long)runtime.recognized_irqs,
                       (unsigned long long)runtime.clock.vblank_events,
                       cpu.pc);
            }
            /* Prior PC-40 stopped naturally at this instruction on
               UNSUPPORTED 88. PC-41 may now execute ADC A,B, but MUST
               arrive at identical source-machine state first. */
            if(route_long && steps==525358ul) {
                if(!ys_pc41_historical_checkpoint(&route,&runtime,steps,
                                                    sprite.counts,
                                                    collision.observed_collision_calls)) {
                    fputs("PC-41 original 525358-step checkpoint drift\n",stderr);
                    free(rom);free(bus);free(vdp);free(sound);
                    return EXIT_FAILURE;
                }
                puts("PC-41 PASS original PC-40 pre-ADC 525358-step"
                     " CPU/mapper/IRQ/selector/sprite checkpoint");
            }
            if(route_long && steps==300000ul &&
               !ys_pc40_route_mark_prefix(&route,&runtime,steps,
                                          sprite.counts,
                                          collision.observed_collision_calls)) {
                fputs("PC-40 missing unchanged 300k source prefix\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            const unsigned pc37_prev_completed=upload.completed;
            const unsigned pc38_prev_entries=upload.entries;
            if((route_long && !ys_pc40_route_sample(&route,&runtime,steps)) ||
               (provenance_audit &&
                !ys_pc_sat_provenance_sample(&provenance,&runtime)) ||
               !ys_pc_source_watch_sample(&collision,&runtime) ||
               (postrelease && !ys_pc_sprite_watch_sample(&sprite,&runtime)) ||
               (upload_audit && !ys_pc_sprite_upload_watch_sample(&upload,&runtime))) {
                fputs("PC-27/33 invalid source event observer\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            const uint8_t selector=ys_sms_bus_read(bus,0xC01Fu);
            if(provenance_audit && upload.entries!=pc38_prev_entries &&
               (upload.entries!=pc38_prev_entries+1u ||
                !ys_pc_sat_provenance_upload(&provenance,&runtime))) {
                fputs("PC-38 cannot trace original SAT WRAM entry\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);
                return EXIT_FAILURE;
            }
            if(frame_audit && upload.completed!=pc37_prev_completed) {
                /* PC-36 proved this event completes exactly 64+128 OUTI;
                   take a full VDP snapshot without changing the interpreter. */
                if(upload.completed!=pc37_prev_completed+1u ||
                   cpu.pc!=0x053Fu || pc37_captures==UINT32_MAX) {
                    fputs("PC-37 invalid completion sequence\n",stderr);
                    free(rom);free(bus);free(vdp);free(sound);
                    return EXIT_FAILURE;
                }
                ++pc37_captures;
                const bool enabled=(vdp->registers[0]&4u)!=0u &&
                                   (vdp->registers[1]&0x40u)!=0u;
                if(enabled) ++pc37_enabled;
                /* Prefer the latest Mode-4 display-enabled sample, or
                   the latest upload if no such sample was observed. */
                if(enabled || pc37_enabled==0u) {
                    pc37_vdp=*vdp;
                    pc37_have=true;
                    pc37_selected_enabled=enabled;
                    pc37_step=steps;
                    pc37_irq=runtime.recognized_irqs;
                    pc37_vblank=runtime.clock.vblank_events;
                    pc37_slot2=bus->mapped_bank[2];
                    pc37_selector=selector;
                }
            }
            if(video_audit) {
                const uint8_t visible=(uint8_t)
                    ((vdp->registers[1] & 0x40u)!=0u);
                if(visible) {
                    ++display_enabled_samples;
                    if(first_display_step==0u)
                        first_display_step=cpu.steps;
                }
                if(visible!=last_display) ++display_transitions;
                if(selector!=last_mode) {
                    ++selector_transitions;
                    if(selector==2u && first_selector2_step==0u)
                        first_selector2_step=cpu.steps;
                }
                if(bus->mapped_bank[2]!=last_slot2)
                    ++slot2_transitions;
                last_display=visible;
                last_mode=selector;
                last_slot2=bus->mapped_bank[2];
            }
            if(cpu.pc==0x0CD1u && selector==0x01u) {
                armed=true;
                if(arm_hits!=UINT32_MAX) ++arm_hits;
            }
            if(cpu.pc==0x0CD1u) {
                last_edge=ys_sms_bus_read(bus,0xC01Cu);
                if(hits_edge!=UINT32_MAX) ++hits_edge;
                if((last_edge&0x10u)!=0u && edge_10_hits!=UINT32_MAX)
                    ++edge_10_hits;
            }
            if(cpu.pc==0x0CC8u && hits_mode_write!=UINT32_MAX) {
                ++hits_mode_write;
                saw_mode_write=true;
            }
            if(pressed && saw_mode_write && selector==0x02u) {
                if(!saw_mode2) mode2_step=cpu.steps;
                saw_mode2=true;
            }
            if(armed && !pressed && cpu.pc==0x0773u) {
                input.dc=0xEFu; /* Button 1, port DC bit 4 active low. */
                pressed=true;press_step=cpu.steps;
            } else if(pressed && !released && cpu.pc==0x0773u) {
                input.dc=0xFFu; /* Release before second sampled IN. */
                released=true;release_step=cpu.steps;
            }
            if(saw_mode2 && released && !postrelease) {
                why="mode2_after_release";break;
            }
            if(collision.observed_collision_calls>0u) {
                why="collision_observed";break;
            }
            if(runtime.clock.vblank_events-start_blank>=blank_budget) {
                why="vblank_limit";break;
            }
            const bool execute_release=
                postrelease && released && !release_sampled &&
                cpu.pc==0x0773u;
            Z80Status state=ys_sms_runtime_step_auto(&runtime);
            if(state!=Z80_RUNNING && state!=Z80_HALTED) {
                why="unsupported";break;
            }
            if(execute_release) release_sampled=true;
        }
        if(route_long) {
            printf("PC-40 source stop: reason=%s steps=%lu"
                   " observations=%lu PC=$%04X IRQ=%llu VBlank=%llu\n",
                   why,steps,route.seen_iterations,cpu.pc,
                   (unsigned long long)runtime.recognized_irqs,
                   (unsigned long long)runtime.clock.vblank_events);
            FILE *route_file=fopen(argv[4],"wb");
            bool ok=route_file && ys_pc40_route_write(route_file,&route,
                                                       &runtime,why,steps);
            if(route_file && fclose(route_file)!=0) ok=false;
            if(!ok) {
                fputs("PC-40 cannot serialize extended original source route\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            printf("PC-40 original 600k extended source route:"
                   " executed=%lu reason=%s PC=$%04X"
                   " prefix=$%04X IRQ=%llu VBlank=%llu\n",
                   steps,why,cpu.pc,route.prefix_pc,
                   (unsigned long long)runtime.recognized_irqs,
                   (unsigned long long)runtime.clock.vblank_events);
        }
        if(pc39_mode) {
            FILE *strobe=fopen(argv[9],"wb");
            bool ok=strobe && ys_pc_sat_strobes_write(strobe,&pc39,
                                                       &runtime,why,steps);
            if(strobe && fclose(strobe)!=0) ok=false;
            if(!ok) {
                fputs("PC-39 cannot write source WRAM strobe audit\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            printf("PC-39 actual source SAT WRAM stores:"
                   " pre=%llu (same=%llu) post=%llu (same=%llu)"
                   " source-sites=%u\n",
                   (unsigned long long)pc39.count[0],
                   (unsigned long long)pc39.same[0],
                   (unsigned long long)pc39.count[1],
                   (unsigned long long)pc39.same[1],pc39.site_count);
        }
        if(provenance_audit) {
            FILE *file=fopen(argv[8],"wb");
            bool ok=file && ys_pc_sat_provenance_write(file,&provenance,
                                                          &runtime,why,steps);
            if(file && fclose(file)!=0) ok=false;
            if(!ok) {
                fputs("PC-38 cannot serialize source SAT provenance\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);
                return EXIT_FAILURE;
            }
            printf("PC-38 original visible SAT mutations: changes=%llu"
                   " unique=%u sites=%u uploads=%u changed_uploads=%u\n",
                   (unsigned long long)provenance.changed,
                   provenance.unique_bytes,provenance.site_count,
                   provenance.upload_count,provenance.changed_uploads);
        }
        if(frame_audit) {
            if(!pc37_have || pc37_captures!=upload.completed) {
                fputs("PC-37 missing original complete SAT snapshot\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            uint8_t *rgb=malloc(YS_SMS_RGB_BYTES);
            YsSmsFrameStats stats={0};
            bool frame_ok=rgb &&
                ys_sms_video_render(&pc37_vdp,rgb,YS_SMS_RGB_BYTES,&stats);
            FILE *frame=frame_ok?fopen(argv[6],"wb"):NULL;
            if(!frame) frame_ok=false;
            if(frame_ok &&
               !ys_sms_video_write_ppm(frame,rgb,YS_SMS_RGB_BYTES))
                frame_ok=false;
            if(frame && fclose(frame)!=0) frame_ok=false;
            FILE *metadata=frame_ok?fopen(argv[7],"wb"):NULL;
            if(!metadata) frame_ok=false;
            if(frame_ok) {
                const uint8_t *reg=pc37_vdp.registers;
                frame_ok= fprintf(metadata,
                    "{\n"
                    " \"schema\":\"ys-pc37-original-vdp-frame-v1\",\n"
                    " \"source\":\"pc34-same-run\","
                    "\"continued_steps\":%lu,\n"
                    " \"stop_pc\":\"%04X\",\"stop_irq\":%llu,"
                    "\"stop_vblank\":%llu,\n"
                    " \"captures\":%u,\"completed\":%u,"
                    "\"display_enabled_captures\":%u,\n"
                    " \"selected_pc\":\"053F\","
                    "\"selected_step\":%lu,"
                    "\"selected_irq\":%llu,\"selected_vblank\":%llu,\n"
                    " \"selected_slot2\":%u,\"selected_selector\":%u,"
                    "\"selected_display_enabled\":%s,\n"
                    " \"reg0\":%u,\"reg1\":%u,"
                    "\"reg5\":%u,\"reg6\":%u,\n"
                    " \"vram_crc32\":%u,\"cram_crc32\":%u,"
                    "\"registers_crc32\":%u,\"rgb_crc32\":%u,\n"
                    " \"sprite_overflow_lines\":%u,"
                    "\"sprite_collision_pixels\":%u\n}\n",
                    steps,cpu.pc,
                    (unsigned long long)runtime.recognized_irqs,
                    (unsigned long long)runtime.clock.vblank_events,
                    pc37_captures,upload.completed,pc37_enabled,
                    pc37_step,(unsigned long long)pc37_irq,
                    (unsigned long long)pc37_vblank,
                    (unsigned)pc37_slot2,(unsigned)pc37_selector,
                    pc37_selected_enabled?"true":"false",
                    (unsigned)reg[0],(unsigned)reg[1],
                    (unsigned)reg[5],(unsigned)reg[6],
                    pc37_crc32(pc37_vdp.vram,YS_VRAM_BYTES),
                    pc37_crc32(pc37_vdp.cram,YS_CRAM_BYTES),
                    pc37_crc32(reg,YS_VDP_REGISTERS),
                    pc37_crc32(rgb,YS_SMS_RGB_BYTES),
                    stats.sprite_overflow_lines,
                    stats.sprite_collision_pixels)>0;
            }
            if(metadata && fclose(metadata)!=0) frame_ok=false;
            free(rgb);
            if(!frame_ok) {
                fputs("PC-37 cannot write source VDP snapshot\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            printf("PC-37 passive VDP frame: SAT=%u display_enabled=%u"
                   " selected_step=%lu selected_enabled=%u\n",
                   pc37_captures,pc37_enabled,pc37_step,
                   (unsigned)pc37_selected_enabled);
        }
        if(upload_audit) {
            FILE *upload_file=fopen(argv[5],"wb");
            bool upload_ok=upload_file &&
                ys_pc_sprite_upload_watch_write(upload_file,&upload,
                                                 &runtime,why,steps);
            if(upload_file && fclose(upload_file)!=0) upload_ok=false;
            if(!upload_ok) {
                fputs("PC-36 cannot write original SAT transfer audit\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            printf("PC-36 full original SAT transfers:"
                   " entries=%u halfway=%u complete=%u matched=%u"
                   " mismatched=%u bytes=%llu different=%llu\n",
                   upload.entries,upload.halfway,upload.completed,
                   upload.matched,upload.mismatched,
                   (unsigned long long)upload.bytes_compared,
                   (unsigned long long)upload.bytes_different);
        }
        if(video_audit) {
            FILE *video_file=fopen(argv[4],"wb");
            bool video_ok=video_file &&
                fprintf(video_file,
                  "{\n"
                  " \"schema\":\"ys-pc35-source-video-dispatch-v1\",\n"
                  " \"source\":\"pc34-same-run\",\n"
                  " \"continued_steps\":%lu,\"stop_reason\":\"%s\",\n"
                  " \"stop_pc\":\"%04X\",\"stop_irq\":%llu,"
                  "\"stop_vblank\":%llu,\n"
                  " \"release_sampled\":%s,"
                  "\"mode2_seen\":%s,\n"
                  " \"selector_transitions\":%llu,"
                  "\"first_selector2_step\":%llu,"
                  "\"stop_selector\":%u,\n"
                  " \"display_transitions\":%llu,"
                  "\"display_enabled_samples\":%llu,"
                  "\"first_display_step\":%llu,"
                  "\"display_enabled_final\":%s,\n"
                  " \"vram_writes_delta\":%llu,"
                  "\"cram_writes_delta\":%llu,\n"
                  " \"slot2_transitions\":%llu,"
                  "\"slot2_final\":%u,\n"
                  " \"sprite_upload0427_hits\":%u,"
                  "\"bank6_sprite9932_hits\":%u,"
                  "\"collision_calls\":%u\n}\n",
                  steps,why,cpu.pc,
                  (unsigned long long)runtime.recognized_irqs,
                  (unsigned long long)runtime.clock.vblank_events,
                  release_sampled?"true":"false",
                  saw_mode2?"true":"false",
                  (unsigned long long)selector_transitions,
                  (unsigned long long)first_selector2_step,
                  (unsigned)ys_sms_bus_read(bus,0xC01Fu),
                  (unsigned long long)display_transitions,
                  (unsigned long long)display_enabled_samples,
                  (unsigned long long)first_display_step,
                  (vdp->registers[1]&0x40u)?"true":"false",
                  (unsigned long long)(vdp->vram_writes-initial_vram),
                  (unsigned long long)(vdp->cram_writes-initial_cram),
                  (unsigned long long)slot2_transitions,
                  (unsigned)bus->mapped_bank[2],
                  sprite.counts[4],sprite.counts[3],
                  collision.observed_collision_calls)>0;
            if(video_file && fclose(video_file)!=0) video_ok=false;
            if(!video_ok) {
                fputs("PC-35 cannot serialize source video audit\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
            printf("PC-35 same source-run video audit: display_samples=%llu"
                   " display_switches=%llu VRAM_delta=%llu CRAM_delta=%llu"
                   " selector_switches=%llu slot2_switches=%llu\n",
                   (unsigned long long)display_enabled_samples,
                   (unsigned long long)display_transitions,
                   (unsigned long long)(vdp->vram_writes-initial_vram),
                   (unsigned long long)(vdp->cram_writes-initial_cram),
                   (unsigned long long)selector_transitions,
                   (unsigned long long)slot2_transitions);
        }
        /* PC-33-only evidence fields; the PC-27 JSON schema is unchanged.
           Two different clocks exist: cpu.steps is absolute since reset,
           but continued_steps starts after the verified M45 checkpoint. */
        char extra[256]="";
        if(postrelease) {
            int written=snprintf(extra,sizeof(extra),
                ",\n  \"release_sampled\":%s,"
                "\n  \"sprite_counts\":[%u,%u,%u,%u,%u]",
                release_sampled?"true":"false",
                sprite.counts[0],sprite.counts[1],sprite.counts[2],
                sprite.counts[3],sprite.counts[4]);
            if(written<0 || (size_t)written>=sizeof(extra)) {
                fputs("PC-33 cannot serialize passive event counts\n",stderr);
                free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
            }
        }
        FILE *output=fopen(argv[3],"wb");
        bool ok=output &&
            fprintf(output,
             "{\n"
             "  \"schema\":\"%s\",\n"
             "  \"start_pc\":\"0C92\",\"start_selector\":%u,\n"
             "  \"stop_reason\":\"%s\",\"continued_steps\":%lu,\n"
             "  \"stop_pc\":\"%04X\",\"stop_selector\":%u,\n"
             "  \"stop_slot1\":%u,\"stop_slot2\":%u,\n"
             "  \"stop_irq\":%llu,\"stop_vblank\":%llu,\n"
             "  \"arm_hits\":%u,\"edge_check_hits\":%u,\n"
             "  \"edge_bit4_hits\":%u,\"last_edge\":%u,\n"
             "  \"mode_write_hits\":%u,\"mode2_seen\":%s,\n"
             "  \"pressed\":%s,\"released\":%s,\n"
             "  \"press_pc\":\"0773\",\"release_pc\":\"0773\",\n"
             "  \"press_step\":%llu,\"release_step\":%llu,\n"
             "  \"mode2_step\":%llu,\n"
             "  \"port_dc\":%u,\"port_dd\":%u,\n"
             "  \"input_reads_dc\":%llu,\"input_reads_dd\":%llu,\n"
             "  \"observed_collision_calls\":%u%s\n}\n",
             route_long?"ys-pc40-long-original-controller-v1":
             extended?"ys-pc34-extended-postrelease-source-watch-v1":
             postrelease?"ys-pc33-postrelease-source-watch-v1":
                         "ys-pc27-original-button-probe-v1",
             (unsigned)start_selector,why,steps,cpu.pc,
             (unsigned)ys_sms_bus_read(bus,0xC01Fu),
             (unsigned)bus->mapped_bank[1],(unsigned)bus->mapped_bank[2],
             (unsigned long long)runtime.recognized_irqs,
             (unsigned long long)runtime.clock.vblank_events,
             arm_hits,hits_edge,edge_10_hits,(unsigned)last_edge,
             hits_mode_write,saw_mode2?"true":"false",
             pressed?"true":"false",released?"true":"false",
             (unsigned long long)press_step,
             (unsigned long long)release_step,
             (unsigned long long)mode2_step,
             (unsigned)input.dc,(unsigned)input.dd,
             (unsigned long long)input.reads_dc,
             (unsigned long long)input.reads_dd,
             collision.observed_collision_calls,extra)>0;
        if(output && fclose(output)!=0) ok=false;
        if(!ok) {
            fputs("PC-27 cannot write original controller experiment\n",stderr);
            free(rom);free(bus);free(vdp);free(sound);return EXIT_FAILURE;
        }
        printf("PC-27/33 source-armed controller experiment:"
               " reason=%s steps=%lu PC=$%04X fault=$%04X status=%u"
               " slot1=%u slot2=%u bytes=%02X_%02X_%02X_%02X"
               " selector=%u->%u arm_hits=%u"
               " edge_bit4=%u mode_write_hits=%u mode2=%u"
               " pressed=%u released=%u IRQ=%llu VBlank=%llu"
               " collisions=%u\n",
               why,steps,cpu.pc,cpu.fault_pc,(unsigned)cpu.status,
               (unsigned)bus->mapped_bank[1],
               (unsigned)bus->mapped_bank[2],
               (unsigned)ys_sms_bus_read(bus,cpu.pc),
               (unsigned)ys_sms_bus_read(bus,(uint16_t)(cpu.pc+1u)),
               (unsigned)ys_sms_bus_read(bus,(uint16_t)(cpu.pc+2u)),
               (unsigned)ys_sms_bus_read(bus,(uint16_t)(cpu.pc+3u)),
               (unsigned)start_selector,
               (unsigned)ys_sms_bus_read(bus,0xC01Fu),
               arm_hits,edge_10_hits,hits_mode_write,(unsigned)saw_mode2,
               (unsigned)pressed,(unsigned)released,
               (unsigned long long)runtime.recognized_irqs,
               (unsigned long long)runtime.clock.vblank_events,
               collision.observed_collision_calls);
        if(postrelease) {
            printf("PC-33/34 source post-release research:"
                   " sampled_release=%u step=%lu"
                   " sprite_caller26F3=%u sprite_mapper26F5=%u"
                   " sprite_upload0427=%u bank6_9932=%u"
                   " source_collision_calls=%u\n",
                   (unsigned)release_sampled,steps,
                   sprite.counts[0],sprite.counts[1],
                   sprite.counts[4],sprite.counts[3],
                   collision.observed_collision_calls);
        }
        puts("PC-27/33/34 research only: controller pulse is experimental;"
             " even a source-proven transition is NOT independent"
             " emulator-match, original gameplay or an Alpha gate");
    } else {
        puts("Stop before source $0C92 video setup, not playable.");
    }











    if (argc==4 && strcmp(argv[2],"--frame")==0) {
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
        printf("PASS saved original Ys ROM VDP state at PC=$0C92: %s"
               " (256x192 PPM; may be blank during initialization)\n",argv[3]);
    }
    free(rom);free(bus);free(vdp);free(sound);
    return EXIT_SUCCESS;
}
