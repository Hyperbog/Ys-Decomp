#include "z80.h"
#include <string.h>

static uint16_t pair(uint8_t hi, uint8_t lo) {
    return (uint16_t)((uint16_t)hi << 8 | lo);
}
static void split(uint16_t value, uint8_t *hi, uint8_t *lo) {
    *hi = (uint8_t)(value >> 8); *lo = (uint8_t)value;
}
static uint8_t fetch(YsZ80 *cpu) {
    uint8_t value = ys_sms_bus_read(cpu->bus, cpu->pc);
    cpu->pc = (uint16_t)(cpu->pc + 1u);
    return value;
}
static uint16_t fetch16(YsZ80 *cpu) {
    uint8_t lo = fetch(cpu), hi = fetch(cpu);
    return pair(hi, lo);
}
static bool store(YsZ80 *cpu, uint16_t address, uint8_t value) {
    if (ys_sms_bus_write(cpu->bus, address, value)) return true;
    cpu->status = Z80_BAD_WRITE; return false;
}
static uint8_t *reg(YsZ80 *cpu, unsigned index) {
    switch (index & 7u) {
    case 0: return &cpu->b;
    case 1: return &cpu->c;
    case 2: return &cpu->d;
    case 3: return &cpu->e;
    case 4: return &cpu->h;
    case 5: return &cpu->l;
    case 7: return &cpu->a;
    default: return NULL;  /* Register 6 is (HL), not a CPU register. */
    }
}
static uint8_t r8(YsZ80 *cpu, unsigned index) {
    uint8_t *r = reg(cpu, index);
    return r ? *r : ys_sms_bus_read(cpu->bus, pair(cpu->h, cpu->l));
}
static bool w8(YsZ80 *cpu, unsigned index, uint8_t value) {
    uint8_t *r = reg(cpu, index);
    if (r) { *r = value; return true; }
    return store(cpu, pair(cpu->h, cpu->l), value);
}
static uint8_t sz53(uint8_t value) {
    return (uint8_t)((value & (Z80_F_S | Z80_F_5 | Z80_F_3)) |
                     (value == 0 ? Z80_F_Z : 0));
}
static bool parity(uint8_t value) {
    unsigned count = 0;
    for (unsigned i = 0; i < 8; ++i) count += (value >> i) & 1u;
    return (count & 1u) == 0;
}
static uint8_t inc_flags(uint8_t old, uint8_t result, uint8_t carry) {
    return (uint8_t)(sz53(result) | carry |
        (((old & 15u) == 15u) ? Z80_F_H : 0) |
        (old == 0x7Fu ? Z80_F_PV : 0));
}
static uint8_t dec_flags(uint8_t old, uint8_t result, uint8_t carry) {
    return (uint8_t)(sz53(result) | carry | Z80_F_N |
        ((old & 15u) == 0 ? Z80_F_H : 0) |
        (old == 0x80u ? Z80_F_PV : 0));
}
static uint8_t sub_flags(uint8_t lhs, uint8_t rhs, uint8_t result) {
    return (uint8_t)(sz53(result) | Z80_F_N |
        ((lhs ^ rhs ^ result) & 0x10u ? Z80_F_H : 0) |
        (((lhs ^ rhs) & (lhs ^ result) & 0x80u) ? Z80_F_PV : 0) |
        (lhs < rhs ? Z80_F_C : 0));
}

/* Z80 8-bit ADD A,r, including carry, half-carry, overflow and X/Y. */
static uint8_t add8_flags(uint8_t lhs, uint8_t rhs, uint8_t result,
                          unsigned full_result) {
    return (uint8_t)(sz53(result) |
        (((lhs & 15u) + (rhs & 15u) > 15u) ? Z80_F_H : 0u) |
        (((~(lhs ^ rhs) & (lhs ^ result)) & 0x80u) ? Z80_F_PV : 0u) |
        (full_result > 0xFFu ? Z80_F_C : 0u));
}

static uint8_t bit_flags(uint8_t flags, uint8_t value, unsigned bit,
                         uint8_t undocumented) {
    bool set=(value & (1u<<bit))!=0;
    return (uint8_t)((flags & Z80_F_C) | Z80_F_H |
        (set?0u:(Z80_F_Z|Z80_F_PV)) |
        (bit==7u && set?Z80_F_S:0u) |
        (undocumented & (Z80_F_3|Z80_F_5)));
}

static bool push16(YsZ80 *cpu, uint16_t value) {
    uint16_t hi = (uint16_t)(cpu->sp - 1u), lo = (uint16_t)(hi - 1u);
    if (!store(cpu, hi, (uint8_t)(value >> 8)) ||
        !store(cpu, lo, (uint8_t)value)) return false;
    cpu->sp = lo; return true;
}
static uint16_t pop16(YsZ80 *cpu) {
    uint8_t lo = ys_sms_bus_read(cpu->bus, cpu->sp++);
    uint8_t hi = ys_sms_bus_read(cpu->bus, cpu->sp++);
    return pair(hi, lo);
}

static void exchange(uint8_t *left, uint8_t *right) {
    uint8_t old=*left; *left=*right; *right=old;
}
void ys_z80_reset(YsZ80 *cpu, YsSmsBus *bus) {
    memset(cpu, 0, sizeof(*cpu));
    cpu->bus = bus;
    cpu->status = Z80_RUNNING;
}

void ys_z80_attach_vdp(YsZ80 *cpu, YsSmsVdp *vdp) {
    if (cpu) cpu->vdp = vdp;
}
void ys_z80_attach_sound(YsZ80 *cpu, YsSmsSound *sound) {
    if (cpu) cpu->sound = sound;
}
void ys_z80_attach_input(YsZ80 *cpu, YsSmsInput *input) {
    if (cpu) cpu->input=input;
}
static bool out_port(YsZ80 *cpu, uint8_t port, uint8_t value) {
    if ((cpu->vdp && ys_sms_vdp_write(cpu->vdp,port,value)) ||
        (cpu->sound && ys_sms_sound_write(cpu->sound,port,value))) return true;
    cpu->status=Z80_UNSUPPORTED_PORT;
    return false;
}

bool ys_z80_irq(YsZ80 *cpu) {
    if (!cpu || !cpu->bus || !cpu->iff1 || cpu->ei_delay ||
        cpu->interrupt_mode!=1 || (cpu->status!=Z80_RUNNING &&
                                     cpu->status!=Z80_HALTED))
        return false;
    /* IM 1: maskable interrupt acknowledges IFF1, vectors to $0038.
       IFF2 is preserved for RETN/NMI semantics. */
    if (!push16(cpu,cpu->pc)) {
        cpu->fault_pc=cpu->pc;
        return false;
    }
    cpu->iff1=false;
    cpu->ei_delay=0;
    cpu->pc=0x0038u;
    cpu->status=Z80_RUNNING;
    return true;
}

/* Documented baseline Z80 T-states for the opcodes this interpreter
   currently implements. Return zero for instructions without a known timing.
   Conditional costs use flags from before execution, never post-call flags.
   This is instruction-granular timing, not VDP bus contention or I/O wait. */
static bool timed_condition(uint8_t opcode, uint8_t f) {
    uint8_t mask = (opcode & 0x30u)==0x00u ? Z80_F_Z :
                   (opcode & 0x30u)==0x10u ? Z80_F_C :
                   (opcode & 0x30u)==0x20u ? Z80_F_PV : Z80_F_S;
    return ((f & mask)!=0u)==((opcode & 0x08u)!=0u);
}
static uint8_t opcode_tstates(const YsZ80 *cpu, uint8_t opcode,
                              uint8_t sub, uint8_t f_before,
                              uint8_t b_before, uint16_t start) {
    if (opcode>=0x40u && opcode<=0x7Fu)
        return opcode==0x76u ? 4u :
               (opcode&7u)==6u || ((opcode>>3)&7u)==6u ? 7u : 4u;
    if ((opcode&0xC7u)==0x06u)
        return ((opcode>>3)&7u)==6u ? 10u : 7u;
    if ((opcode&0xC7u)==0x04u || (opcode&0xC7u)==0x05u)
        return ((opcode>>3)&7u)==6u ? 11u : 4u;
    if (opcode>=0x80u && opcode<=0xBFu)
        return (opcode&7u)==6u ? 7u : 4u;
    if ((opcode&0xC7u)==0xC7u) return 11u; /* RST $00-$38 */
    if ((opcode&0xCFu)==0x09u) return 11u; /* ADD HL,rr */
    if ((opcode&0xC7u)==0xC0u)
        return timed_condition(opcode,f_before) ? 11u : 5u; /* RET cc */
    if ((opcode&0xC7u)==0xC4u)
        return timed_condition(opcode,f_before) ? 17u : 10u; /* CALL cc */
    if ((opcode&0xC7u)==0xC2u) return 10u; /* JP cc */
    switch(opcode) {
    case 0x00: case 0x08: case 0x2F: case 0xD9:
    case 0xF3: case 0xFB: return 4u;
    case 0xCB: return (sub&7u)==6u ? 12u : 8u; /* BIT b,r */
    case 0xDD: case 0xFD:
        switch(sub) {
        case 0xE5: return 15u; /* PUSH IX/IY */
        case 0xE1: return 14u; /* POP IX/IY */
        case 0x21: return 14u; /* LD IX/IY,nn */
        case 0x09: case 0x19: case 0x29: case 0x39:
            return 15u;       /* ADD IX/IY,rr */
        case 0xCB: return 20u;/* BIT b,(IX/IY+d) */
        default: return 0u;
        }
    case 0x02: case 0x0A: case 0x12: case 0x1A: return 7u;
    case 0x01: case 0x11: case 0x21: case 0x31: return 10u;
    case 0x03: case 0x13: case 0x23:
    case 0x0B: case 0x1B: case 0x2B: return 6u;
    case 0x22: case 0x2A: return 16u;
    case 0x32: case 0x3A: return 13u;
    case 0xE6: case 0xF6: case 0xFE: return 7u;
    case 0xC3: return 10u;
    case 0xE9: return 4u;
    case 0xC9: return 10u;
    case 0xCD: return 17u;
    case 0xC5: case 0xD5: case 0xE5: case 0xF5: return 11u;
    case 0xC1: case 0xD1: case 0xE1: case 0xF1: return 10u;
    case 0x10: return (uint8_t)(b_before!=1u ? 13u : 8u);
    case 0x18: return 12u;
    case 0x20: case 0x28:
        return ((f_before & Z80_F_Z)!=0u)==(opcode==0x28u)?12u:7u;
    case 0x30: case 0x38:
        return ((f_before & Z80_F_C)!=0u)==(opcode==0x38u)?12u:7u;
    case 0xD3: case 0xDB: return 11u;
    case 0xED:
        if (sub==0x56u) return 8u; /* IM 1 */
        if (sub==0x45u || sub==0x4Du) return 14u; /* RETN/RETI */
        if (sub==0x6Fu) return 18u; /* RLD */
        if (sub==0xA0u || sub==0xA3u || sub==0xABu) return 16u;
        if (sub==0xB0u) return cpu->pc==start ? 21u : 16u; /* LDIR */
        if ((sub&0xC7u)==0x41u && sub!=0x71u) return 12u;
        return 0u;
    default: return 0u;
    }
}

Z80Status ys_z80_step(YsZ80 *cpu) {
    if (!cpu || !cpu->bus) return Z80_UNSUPPORTED;
    if (cpu->status != Z80_RUNNING) return cpu->status;
    uint16_t start = cpu->pc;
    cpu->last_tstates=0u;
    uint8_t f_before=cpu->f, b_before=cpu->b;
    uint8_t opcode = fetch(cpu);
    uint8_t timing_sub=(opcode==0xCBu || opcode==0xDDu ||
                        opcode==0xFDu || opcode==0xEDu) ?
                        ys_sms_bus_read(cpu->bus,cpu->pc) : 0u;
    if (opcode >= 0x40u && opcode <= 0x7Fu) {
        if (opcode == 0x76u) cpu->status = Z80_HALTED;
        else if (!w8(cpu, (opcode >> 3) & 7u, r8(cpu, opcode & 7u)))
            goto fail;
    } else if ((opcode & 0xC7u) == 0x06u) {
        if (!w8(cpu, (opcode >> 3) & 7u, fetch(cpu))) goto fail;
    } else if ((opcode & 0xC7u) == 0x04u) {
        unsigned i = (opcode >> 3) & 7u;
        uint8_t old = r8(cpu, i), result = (uint8_t)(old + 1u);
        if (!w8(cpu, i, result)) goto fail;
        cpu->f = inc_flags(old, result, cpu->f & Z80_F_C);
    } else if ((opcode & 0xC7u) == 0x05u) {
        unsigned i = (opcode >> 3) & 7u;
        uint8_t old = r8(cpu, i), result = (uint8_t)(old - 1u);
        if (!w8(cpu, i, result)) goto fail;
        cpu->f = dec_flags(old, result, cpu->f & Z80_F_C);
    } else if (opcode>=0xB8u && opcode<=0xBFu) {
        uint8_t rhs=r8(cpu,opcode&7u);
        cpu->f=sub_flags(cpu->a,rhs,(uint8_t)(cpu->a-rhs));
    } else if (opcode>=0xA0u && opcode<=0xA7u) {
        cpu->a=(uint8_t)(cpu->a & r8(cpu,opcode&7u));
        cpu->f=(uint8_t)(sz53(cpu->a)|Z80_F_H|
                         (parity(cpu->a)?Z80_F_PV:0));
    } else if (opcode>=0xA8u && opcode<=0xAFu) {
        cpu->a=(uint8_t)(cpu->a ^ r8(cpu,opcode&7u));
        cpu->f=(uint8_t)(sz53(cpu->a)|
                         (parity(cpu->a)?Z80_F_PV:0));
    } else if (opcode>=0xB0u && opcode<=0xB7u) {
        cpu->a=(uint8_t)(cpu->a | r8(cpu,opcode&7u));
        cpu->f=(uint8_t)(sz53(cpu->a)|
                         (parity(cpu->a)?Z80_F_PV:0));
    } else if (opcode>=0x80u && opcode<=0x87u) {
        uint8_t rhs=r8(cpu,opcode&7u);
        uint8_t old=cpu->a;
        unsigned full=(unsigned)old+rhs;
        cpu->a=(uint8_t)full;
        cpu->f=add8_flags(old,rhs,cpu->a,full);
    } else if ((opcode & 0xC7u)==0xC7u) {
        /* One-byte RST vectors; execute the original bank-0 dispatch helper. */
        if(!push16(cpu,cpu->pc)) goto fail;
        cpu->pc=(uint16_t)(opcode&0x38u);
    } else if ((opcode & 0xCFu) == 0x09u) {
        uint16_t hl=pair(cpu->h,cpu->l);
        unsigned index=(opcode >> 4) & 3u;
        uint16_t rhs=index==0 ? pair(cpu->b,cpu->c) :
                     index==1 ? pair(cpu->d,cpu->e) :
                     index==2 ? hl : cpu->sp;
        unsigned sum=(unsigned)hl+rhs;
        uint16_t result=(uint16_t)sum;
        split(result,&cpu->h,&cpu->l);
        cpu->f=(uint8_t)((cpu->f&(Z80_F_S|Z80_F_Z|Z80_F_PV)) |
            ((result>>8)&(Z80_F_3|Z80_F_5)) |
            (((hl&0xFFFu)+(rhs&0xFFFu)>0xFFFu)? Z80_F_H:0) |
            (sum>0xFFFFu? Z80_F_C:0));
    } else switch (opcode) {
    case 0x00: break; /* NOP */
    case 0xCB: {
        uint8_t operation=fetch(cpu);
        if ((operation & 0xC0u)!=0x40u) {
            cpu->status=Z80_UNSUPPORTED;goto fail;
        }
        uint8_t value=r8(cpu,operation&7u);
        cpu->f=bit_flags(cpu->f,value,(operation>>3)&7u,value);
        break;
    }
    case 0x2F: /* CPL: SZPV/C unchanged; set H/N, 3/5 from A. */
        cpu->a=(uint8_t)~cpu->a;
        cpu->f=(uint8_t)((cpu->f & (Z80_F_S|Z80_F_Z|Z80_F_PV|Z80_F_C)) |
            (cpu->a & (Z80_F_3|Z80_F_5)) | Z80_F_H | Z80_F_N);
        break;
    case 0x08:
        exchange(&cpu->a,&cpu->a_alt);
        exchange(&cpu->f,&cpu->f_alt);
        break; /* EX AF,AF' */
    case 0xD9:
        exchange(&cpu->b,&cpu->b_alt); exchange(&cpu->c,&cpu->c_alt);
        exchange(&cpu->d,&cpu->d_alt); exchange(&cpu->e,&cpu->e_alt);
        exchange(&cpu->h,&cpu->h_alt); exchange(&cpu->l,&cpu->l_alt);
        break; /* EXX */
    case 0xDD: case 0xFD: {
        uint8_t sub=fetch(cpu);
        uint16_t *index=opcode==0xDD ? &cpu->ix : &cpu->iy;
        if(sub==0xE5) {
            if(!push16(cpu,*index)) goto fail;
        } else if(sub==0xE1) {
            *index=pop16(cpu);
        } else if(sub==0x21) {
            *index=fetch16(cpu);
        } else if(sub==0x09 || sub==0x19 || sub==0x29 || sub==0x39) {
            uint16_t rhs=sub==0x09?pair(cpu->b,cpu->c):
                         sub==0x19?pair(cpu->d,cpu->e):
                         sub==0x29?*index:cpu->sp;
            unsigned sum=(unsigned)*index+rhs;
            uint16_t next=(uint16_t)sum;
            cpu->f=(uint8_t)((cpu->f&(Z80_F_S|Z80_F_Z|Z80_F_PV)) |
                ((next>>8)&(Z80_F_3|Z80_F_5)) |
                (((*index&0xFFFu)+(rhs&0xFFFu)>0xFFFu)?Z80_F_H:0) |
                (sum>0xFFFFu?Z80_F_C:0));
            *index=next;
        } else if(sub==0xCB) {
            int8_t displacement=(int8_t)fetch(cpu);
            uint8_t operation=fetch(cpu);
            if ((operation&0xC7u)!=0x46u) {
                cpu->status=Z80_UNSUPPORTED;goto fail;
            }
            uint16_t addr=(uint16_t)(*index+displacement);
            uint8_t value=ys_sms_bus_read(cpu->bus,addr);
            /* On indexed BIT, undocumented F3/F5 come from address high. */
            cpu->f=bit_flags(cpu->f,value,(operation>>3)&7u,
                              (uint8_t)(addr>>8));
        } else {
            cpu->status=Z80_UNSUPPORTED;goto fail;
        }
        break;
    }
    case 0x02: if (!store(cpu,pair(cpu->b,cpu->c),cpu->a)) goto fail;break;
    case 0x0A: cpu->a=ys_sms_bus_read(cpu->bus,pair(cpu->b,cpu->c));break;
    case 0x12: if (!store(cpu,pair(cpu->d,cpu->e),cpu->a)) goto fail;break;
    case 0x1A: cpu->a=ys_sms_bus_read(cpu->bus,pair(cpu->d,cpu->e));break;
    case 0x01: split(fetch16(cpu), &cpu->b, &cpu->c); break;
    case 0x11: split(fetch16(cpu), &cpu->d, &cpu->e); break;
    case 0x21: split(fetch16(cpu), &cpu->h, &cpu->l); break;
    case 0x31: cpu->sp = fetch16(cpu); break;
    case 0x03: split((uint16_t)(pair(cpu->b,cpu->c)+1u),&cpu->b,&cpu->c); break;
    case 0x13: split((uint16_t)(pair(cpu->d,cpu->e)+1u),&cpu->d,&cpu->e); break;
    case 0x23: split((uint16_t)(pair(cpu->h,cpu->l)+1u),&cpu->h,&cpu->l); break;
    case 0x0B: split((uint16_t)(pair(cpu->b,cpu->c)-1u),&cpu->b,&cpu->c); break;
    case 0x1B: split((uint16_t)(pair(cpu->d,cpu->e)-1u),&cpu->d,&cpu->e); break;
    case 0x2B: split((uint16_t)(pair(cpu->h,cpu->l)-1u),&cpu->h,&cpu->l); break;
    case 0x22: {
        uint16_t at = fetch16(cpu);
        if (!store(cpu,at,cpu->l) || !store(cpu,(uint16_t)(at+1u),cpu->h)) goto fail;
        break;
    }
    case 0x2A: {
        uint16_t at = fetch16(cpu);
        uint8_t lo=ys_sms_bus_read(cpu->bus,at);
        uint8_t hi=ys_sms_bus_read(cpu->bus,(uint16_t)(at+1u));
        cpu->h=hi;cpu->l=lo; break;
    }
    case 0x32: if (!store(cpu,fetch16(cpu),cpu->a)) goto fail; break;
    case 0x3A: cpu->a=ys_sms_bus_read(cpu->bus,fetch16(cpu)); break;
    case 0xAF: cpu->a=0;cpu->f=Z80_F_Z|Z80_F_PV;break;
    case 0xE6: cpu->a=(uint8_t)(cpu->a & fetch(cpu));
        cpu->f=(uint8_t)(sz53(cpu->a)|Z80_F_H|(parity(cpu->a)?Z80_F_PV:0));
        break;
    case 0xF6: cpu->a=(uint8_t)(cpu->a | fetch(cpu));
        cpu->f=(uint8_t)(sz53(cpu->a)|(parity(cpu->a)?Z80_F_PV:0));
        break;
    case 0xBE: {
        uint8_t rhs=ys_sms_bus_read(cpu->bus,pair(cpu->h,cpu->l));
        cpu->f=sub_flags(cpu->a,rhs,(uint8_t)(cpu->a-rhs));break;
    }
    case 0xA7: cpu->f=(uint8_t)(sz53(cpu->a)|Z80_F_H|
                                      (parity(cpu->a)?Z80_F_PV:0));break;
    case 0xB7: cpu->f=(uint8_t)(sz53(cpu->a)|
                                      (parity(cpu->a)?Z80_F_PV:0));break;
    case 0xFE: {
        uint8_t rhs=fetch(cpu);
        cpu->f=sub_flags(cpu->a,rhs,(uint8_t)(cpu->a-rhs));break;
    }
    case 0xE9: cpu->pc=pair(cpu->h,cpu->l);break;
    case 0xC3: cpu->pc=fetch16(cpu);break;
    case 0xC2: case 0xCA: case 0xD2: case 0xDA:
    case 0xE2: case 0xEA: case 0xF2: case 0xFA: {
        uint16_t target=fetch16(cpu);
        uint8_t mask=opcode==0xC2 || opcode==0xCA ? Z80_F_Z :
                     opcode==0xD2 || opcode==0xDA ? Z80_F_C :
                     opcode==0xE2 || opcode==0xEA ? Z80_F_PV : Z80_F_S;
        bool set=(cpu->f & mask)!=0;
        if(set==((opcode & 0x08u)!=0)) cpu->pc=target;
        break;
    }
    case 0xC9: cpu->pc=pop16(cpu);break;
    case 0xC0: case 0xC8: case 0xD0: case 0xD8:
    case 0xE0: case 0xE8: case 0xF0: case 0xF8: {
        uint8_t mask=(opcode&0x30u)==0x00u ? Z80_F_Z :
                     (opcode&0x30u)==0x10u ? Z80_F_C :
                     (opcode&0x30u)==0x20u ? Z80_F_PV : Z80_F_S;
        bool expected=(opcode & 0x08u)!=0;
        if(((cpu->f&mask)!=0)==expected) cpu->pc=pop16(cpu);
        break;
    }
    case 0xC4: case 0xCC: case 0xD4: case 0xDC:
    case 0xE4: case 0xEC: case 0xF4: case 0xFC: {
        uint16_t target=fetch16(cpu);
        uint8_t mask=(opcode&0x30u)==0x00u?Z80_F_Z:
                     (opcode&0x30u)==0x10u?Z80_F_C:
                     (opcode&0x30u)==0x20u?Z80_F_PV:Z80_F_S;
        bool expected=(opcode&0x08u)!=0;
        if(((cpu->f&mask)!=0)==expected) {
            if(!push16(cpu,cpu->pc)) goto fail;
            cpu->pc=target;
        }
        break;
    }
    case 0xCD: {
        uint16_t target=fetch16(cpu);
        if (!push16(cpu,cpu->pc)) goto fail;
        cpu->pc=target;break;
    }
    case 0xC5: if (!push16(cpu,pair(cpu->b,cpu->c))) goto fail;break;
    case 0xD5: if (!push16(cpu,pair(cpu->d,cpu->e))) goto fail;break;
    case 0xE5: if (!push16(cpu,pair(cpu->h,cpu->l))) goto fail;break;
    case 0xF5: if (!push16(cpu,pair(cpu->a,cpu->f))) goto fail;break;
    case 0xC1: split(pop16(cpu),&cpu->b,&cpu->c);break;
    case 0xD1: split(pop16(cpu),&cpu->d,&cpu->e);break;
    case 0xE1: split(pop16(cpu),&cpu->h,&cpu->l);break;
    case 0xF1: split(pop16(cpu),&cpu->a,&cpu->f);break;
    case 0x10: {
        int8_t displacement=(int8_t)fetch(cpu);
        cpu->b=(uint8_t)(cpu->b-1u);
        if(cpu->b) cpu->pc=(uint16_t)(cpu->pc+displacement);
        break;
    }
    case 0xEF: /* RST $28 -- VDP command helper in Ys bank 0. */
        if(!push16(cpu,cpu->pc)) goto fail;
        cpu->pc=0x0028u;break;
    case 0x18: {
        int8_t displacement=(int8_t)fetch(cpu);
        cpu->pc=(uint16_t)(cpu->pc+displacement);break;
    }
    case 0x20: case 0x28: case 0x30: case 0x38: {
        int8_t displacement=(int8_t)fetch(cpu);
        bool take = opcode==0x20 ? !(cpu->f & Z80_F_Z) :
                    opcode==0x28 ? !!(cpu->f & Z80_F_Z) :
                    opcode==0x30 ? !(cpu->f & Z80_F_C) : !!(cpu->f & Z80_F_C);
        if(take) cpu->pc=(uint16_t)(cpu->pc+displacement);
        break;
    }
    case 0xF3: cpu->iff1=false;cpu->iff2=false;break;
    case 0xFB: cpu->iff1=true;cpu->iff2=true;cpu->ei_delay=2;break;
    case 0xED: {
        uint8_t sub=fetch(cpu);
        if (sub==0x56) {cpu->interrupt_mode=1;break;}
        if (sub==0x45 || sub==0x4D) {
            cpu->pc=pop16(cpu);
            if(sub==0x45) cpu->iff1=cpu->iff2; /* RETN */
            break;
        }
        if (sub==0x6F) { /* RLD: A low nibble <- (HL) high nibble,
                            (HL) <- old (HL) low nibble : A low nibble. */
            uint16_t hl=pair(cpu->h,cpu->l);
            uint8_t mem=ys_sms_bus_read(cpu->bus,hl);
            uint8_t next=(uint8_t)((mem<<4)|(cpu->a&0x0Fu));
            uint8_t next_a=(uint8_t)((cpu->a&0xF0u)|(mem>>4));
            if(!store(cpu,hl,next)) goto fail;
            cpu->a=next_a;
            cpu->f=(uint8_t)((cpu->f&Z80_F_C)|sz53(cpu->a)|
                              (parity(cpu->a)?Z80_F_PV:0));
            break;
        }
        if (sub==0xA0) { /* LDI: preserve S,Z,C; update PV and 3/5. */
            uint16_t hl=pair(cpu->h,cpu->l),de=pair(cpu->d,cpu->e);
            uint8_t value=ys_sms_bus_read(cpu->bus,hl);
            if (!store(cpu,de,value)) goto fail;
            split((uint16_t)(hl+1u),&cpu->h,&cpu->l);
            split((uint16_t)(de+1u),&cpu->d,&cpu->e);
            uint16_t bc=(uint16_t)(pair(cpu->b,cpu->c)-1u);
            split(bc,&cpu->b,&cpu->c);
            uint8_t u=(uint8_t)(cpu->a+value);
            cpu->f=(uint8_t)((cpu->f&(Z80_F_S|Z80_F_Z|Z80_F_C)) |
                    (bc ? Z80_F_PV : 0u) | (u & Z80_F_3) |
                    ((u & 2u)<<4));
            break;
        }
        if (sub==0xAB) { /* OUTD: send (HL) to port C, decrement HL and B. */
            uint16_t hl=pair(cpu->h,cpu->l);
            uint8_t value=ys_sms_bus_read(cpu->bus,hl);
            if(!out_port(cpu,cpu->c,value)) goto fail;
            split((uint16_t)(hl-1u),&cpu->h,&cpu->l);
            cpu->b=(uint8_t)(cpu->b-1u);
            unsigned k=(unsigned)cpu->l+value;
            cpu->f=(uint8_t)(sz53(cpu->b) |
                ((value&0x80u)?Z80_F_N:0) |
                ((k>0xFFu)?(Z80_F_H|Z80_F_C):0) |
                (parity((uint8_t)((k&7u)^cpu->b))?Z80_F_PV:0));
            break;
        }
        if (sub==0xA3) { /* OUTI: write at (HL), increment HL, decrement B. */
            uint16_t hl=pair(cpu->h,cpu->l);
            uint8_t value=ys_sms_bus_read(cpu->bus,hl);
            if(!out_port(cpu,cpu->c,value)) goto fail;
            split((uint16_t)(hl+1u),&cpu->h,&cpu->l);
            cpu->b=(uint8_t)(cpu->b-1u);
            unsigned k=(unsigned)cpu->l+value;
            cpu->f=(uint8_t)(sz53(cpu->b)|(value&0x80u?Z80_F_N:0) |
                    (k>255u?(Z80_F_H|Z80_F_C):0) |
                    (parity((uint8_t)(((k&7u)^cpu->b)))?Z80_F_PV:0));
            break;
        }
        if ((sub&0xC7u)==0x41u && sub!=0x71u) {
            if(!out_port(cpu,cpu->c,r8(cpu,(sub>>3)&7u))) goto fail;
            break;
        }
        if (sub==0xB0) {
            uint16_t hl=pair(cpu->h,cpu->l), de=pair(cpu->d,cpu->e);
            uint16_t bc=pair(cpu->b,cpu->c);
            if (!store(cpu,de,ys_sms_bus_read(cpu->bus,hl))) goto fail;
            split((uint16_t)(hl+1u),&cpu->h,&cpu->l);
            split((uint16_t)(de+1u),&cpu->d,&cpu->e);
            split((uint16_t)(bc-1u),&cpu->b,&cpu->c);
            cpu->f=(uint8_t)((cpu->f & (Z80_F_S|Z80_F_Z|Z80_F_C)) |
                (bc!=1 ? Z80_F_PV : 0)); /* H,N reset; flags 3,5 deferred. */
            if (bc!=1) cpu->pc=start; /* Z80 LDIR repeats until BC reaches 0. */
            break;
        }
        cpu->status=Z80_UNSUPPORTED;goto fail;
    }
    case 0xD3: {
        uint8_t port=fetch(cpu);
        if (!out_port(cpu,port,cpu->a)) goto fail;
        break;
    }
    case 0xDB: {
        uint8_t port=fetch(cpu), value=0;
        if (!((cpu->vdp && ys_sms_vdp_read(cpu->vdp,port,&value)) ||
              (cpu->input && ys_sms_input_read(cpu->input,port,&value)))) {
            cpu->status=Z80_UNSUPPORTED_PORT;goto fail;
        }
        cpu->a=value;break; /* IN A,(n) leaves Z80 flags unchanged. */
    }
    default: cpu->status=Z80_UNSUPPORTED;goto fail;
    }
    cpu->last_tstates=opcode_tstates(cpu,opcode,timing_sub,f_before,
                                      b_before,start);
    cpu->total_tstates+=cpu->last_tstates;
    ++cpu->steps;
    if (cpu->ei_delay) --cpu->ei_delay;
    return cpu->status;
fail:
    cpu->last_tstates=0;
    cpu->fault_pc=start;
    cpu->pc=start; /* Fail closed: identify original opcode address. */
    return cpu->status;
}

Z80Status ys_z80_run_until(YsZ80 *cpu, uint16_t stop_pc, uint64_t budget) {
    if (!cpu || !cpu->bus) return Z80_UNSUPPORTED;
    while(cpu->status==Z80_RUNNING && cpu->pc!=stop_pc && budget-- > 0)
        (void)ys_z80_step(cpu);
    if(cpu->status==Z80_RUNNING && cpu->pc!=stop_pc)
        cpu->status=Z80_STEP_LIMIT;
    return cpu->status;
}

const char *ys_z80_status_name(Z80Status status) {
    switch(status) {
    case Z80_RUNNING: return "running";
    case Z80_HALTED: return "halted";
    case Z80_UNSUPPORTED: return "unsupported opcode";
    case Z80_BAD_WRITE: return "ROM write rejected";
    case Z80_UNSUPPORTED_PORT: return "unsupported I/O port";
    case Z80_STEP_LIMIT: return "instruction budget exceeded";
    }
    return "invalid status";
}
